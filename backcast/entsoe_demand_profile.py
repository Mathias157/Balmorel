"""Quickfix: electricity demand profiles from observed ENTSO-E load.

The weather-year demand profiles in data/DE_VAR_T.inc are corrupt for 2022
onwards (weatheryear_inputs_2023/demand_data/classic_demand.csv): LV and LT are
negative almost every hour, the UK, ES, IT and BE have negative hours, and NL,
EE and SK have spikes of 20-60x the median, which made NL demand peak at
136 GW in the backcast. Sub-areas also carry copies of the national profile.

This writes data/DE_VAR_T_ENTSOE.inc with the hourly ENTSO-E actual load of
the backcast year, on the Backcast Calendar, for the OTHER and RESE users of
every region with ENTSO-E load data, and adds its $include to the end of
data/DE_VAR_T.inc if it is missing. Balmorel scales DE_VAR_T to the annual DE,
so only the shape matters. Regions without ENTSO-E load keep their
weather-year profile, with implausible hours interpolated, or base's profile
if too many hours are implausible.

Run from the repository root, after run_weatheryear.py (which overwrites
DE_VAR_T.inc and so drops the $include):
    pixi run python backcast/entsoe_demand_profile.py 2023
"""
import re
import shutil
import sys
from pathlib import Path

import gams.transfer as gt
import pandas as pd

from pybalmorel.backcasting.__main__ import format_entsoe_data
from pybalmorel.backcasting.calendar import SEASONS, TERMS, to_backcast_grid
from pybalmorel.entsoe import bidding_zone_translation

year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
scenario = Path("backcast")
users = ["OTHER", "RESE"]

# Hours outside [LOW, HIGH] x the region's median are implausible and get
# interpolated; a region with more than MAX_BAD_SHARE of them is not used
LOW, HIGH = 0.2, 3.0
MAX_BAD_SHARE = 0.02

include_lines = [
    "$if EXIST '../data/DE_VAR_T_ENTSOE.inc' $INCLUDE '../data/DE_VAR_T_ENTSOE.inc';"
]


def clean(grid: pd.DataFrame) -> tuple[pd.Series, int]:
    """Interpolate implausible or missing hours of an S x T profile.

    Returns the profile in (S,T) order and the number of hours replaced.
    """
    values = grid.stack()
    median = values.median()
    bad = values.isna() | (values < LOW * median) | (values > HIGH * median)
    cleaned = values.mask(bad).interpolate(limit_direction="both")
    return cleaned, int(bad.sum())


# Balmorel regions with electricity demand
gams_dir = Path(shutil.which("gams")).parent
container = gt.Container(system_directory=str(gams_dir))
container.read(str(scenario / "model/backcast_input_data.gdx"), symbols=["DE"])
regions = sorted(container["DE"].records.iloc[:, 1].unique())

# Hourly ENTSO-E load per canonical region. Bidding zones are summed (IT-* to
# IT), and an hour missing in one zone is missing for the region
files = sorted((scenario / "entsoedata").glob(f"{year}_*_load.csv"))
zones = pd.concat(
    [format_entsoe_data(pd.read_csv(file), "h", file, year, "load") for file in files]
).pivot_table(index="Time", columns="Region", values="Value")
zone_region = zones.columns.to_series().replace(bidding_zone_translation)
entsoe_load = pd.DataFrame(
    {
        region: zones[list(group)].sum(axis=1, skipna=False)
        for region, group in zone_region.groupby(zone_region).groups.items()
    }
)

# Current weather-year profiles, for regions without ENTSO-E load
pattern = re.compile(
    r"^DE_VAR_T\('([^']+)', '([^']+)', '(S\d+)', '(T\d+)'\) = ([^;]+);", re.M
)
weatheryear = pd.DataFrame(
    pattern.findall((scenario / "data/DE_VAR_T.inc").read_text()),
    columns=["Region", "User", "Season", "Term", "Value"],
)
weatheryear = weatheryear[weatheryear.User == "OTHER"].astype({"Value": float})

profiles, report = {}, []
for region in regions:
    key = bidding_zone_translation.get(region, region)
    if key in entsoe_load.columns:
        grid = to_backcast_grid(entsoe_load[key], year)
        source = f"ENTSO-E {key}"
    elif region in weatheryear.Region.values:
        grid = (
            weatheryear[weatheryear.Region == region]
            .pivot(index="Season", columns="Term", values="Value")
            .reindex(index=SEASONS, columns=TERMS)
        )
        source = "weather year"
    else:
        report.append(f"{region}: no ENTSO-E load or weather-year profile, keeps base")
        continue

    profile, n_bad = clean(grid)
    if n_bad > MAX_BAD_SHARE * len(profile):
        report.append(f"{region}: {source} has {n_bad} implausible hours, keeps base")
        continue
    profiles[region] = profile
    report.append(f"{region}: {source}, {n_bad} hours interpolated")

lines = [
    f"* Electricity demand profiles for {year} from ENTSO-E actual load, written by",
    "* backcast/entsoe_demand_profile.py - generated, do not hand-edit.",
    *[f"* {line}" for line in report],
]
for region, profile in profiles.items():
    for (season, term), value in profile.items():
        lines.append(f"DE_VAR_T('{region}','OTHER','{season}','{term}')={value:.2f};")
    for user in users[1:]:
        lines.append(f"DE_VAR_T('{region}','{user}',SSS,TTT)=DE_VAR_T('{region}','OTHER',SSS,TTT);")
(scenario / "data/DE_VAR_T_ENTSOE.inc").write_text("\n".join(lines) + "\n")

de_var_t = scenario / "data/DE_VAR_T.inc"
text = de_var_t.read_text()
if include_lines[0] not in text:
    de_var_t.write_text(text.rstrip("\n") + "\n\n" + "\n".join(include_lines) + "\n")
    print(f"Added the $include of DE_VAR_T_ENTSOE.inc to {de_var_t}")

print("\n".join(report))
print(f"Wrote {len(profiles)} regions to {scenario / 'data/DE_VAR_T_ENTSOE.inc'}")
