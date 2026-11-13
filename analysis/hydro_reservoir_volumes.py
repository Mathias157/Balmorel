"""Reservoir volumes scaled down to the ENTSO-E observed filling of a year.

In Balmorel, the reservoir volume of an area is the sum over its reservoir
hydro of GKFX x HYRSMAXVOL_G (MWh). QHYRSMINVOL/QHYRSMAXVOL bound the level
at each season start between HYRSDATA's HYRSMINVOL(s) and HYRSMAXVOL(s)
times that volume. The highest level the model can reach is therefore
max_s HYRSMAXVOL(s) x volume. This is 0.95 x volume on the continent; the
Nordic areas have seasonal envelopes.

ENTSO-E 16.1.D reports the weekly stored energy in reservoirs and hydro
storage per zone. Where a region's highest reachable level exceeds the
year's observed maximum, HYRSMAXVOL_G of all the region's areas is scaled
by one factor, so that the two are equal. Regions below the observed
maximum are reported and left as they are. Regions without ENTSO-E data
keep their volume.

By default, only regions with a flat HYRSDATA envelope are cut. There the
volume is the only limit on the level. The Nordic areas have seasonal
envelopes (historical weekly min and max levels), and their volumes match
the physical capacity (NVE), which reservoirs don't fill in an average
year. In 2023, cutting them made the observed trajectory exceed the scaled
ceiling in more weeks (NO2 0 -> 4, SE2 0 -> 3, SE3 19 -> 23), so
--seasonal is off by default. The table reports their factors and weeks
outside the envelope either way.

Two things limit what the observed maximum means:
- It is a lower bound on the physical volume, because a dry year doesn't
  fill the reservoirs (ES in 2023). The result is therefore a calibration
  for a backcast of that year, and the default output is the backcast's
  data folder, not base. Prospective runs would need a multi-year maximum.
- Some countries include pumped-storage basins in 16.1.D, which Balmorel
  models separately. In those countries the cut is smaller than it could be.

Smaller volumes can't make the model infeasible. QHYRSSEQ is an inequality,
so inflow that doesn't fit is spilled.

Future: this may become part of the year-aligned hydro step in
analysis/hydro_mc_curves.py (which is to move to pybalmorel.entsoe). That
step takes the same year and zones. It could write the volume next to the
MC curves.

Run from the repo root:
    pixi run python analysis/hydro_reservoir_volumes.py 2023
It writes backcast/data/HYRSMAXVOL_G.inc. That file includes base's
HYRSMAXVOL_G.inc and scales the cut areas, as backcast/data/GKFX.inc does
for GKFX.
"""

import sys
from pathlib import Path

import click
import pandas as pd
from hydro_mc_curves import (
    GKFX_ROW,
    read_area_regions,
    reservoir_volumes,
    table_rows,
)
from pybalmorel.entsoe import (
    bidding_zone_translation,
    fetch_annual_data,
    get_api_key,
    read_no_data_zones,
    region_to_entsoe_code,
)

QUERY = "aggregate_water_reservoirs_and_hydro_storage"
BASE_INCLUDE = "../../base/data/HYRSMAXVOL_G.inc"  # as the model folder sees it


def entsoe_code(region: str) -> str:
    """The ENTSO-E area to query for a Balmorel region (DE4-S -> DE_LU)."""
    return region_to_entsoe_code(bidding_zone_translation.get(region, region))


def observed_filling(path: Path, year: int, code: str) -> pd.Series | None:
    """Weekly stored energy (MWh) of `code` within `year`, None without data."""
    f = path / f"{year}_{code}_{QUERY}.csv"
    if not f.exists():
        return None
    s = pd.read_csv(f, index_col=0).iloc[:, 0]
    # Stamped Monday 00:00 Brussels time (Sunday 23:00 in the csv's UTC)
    s.index = pd.to_datetime(s.index, utc=True).tz_convert("Europe/Brussels")
    s = s[(s.index.year == year) & (s > 0)]
    return s if len(s) else None


def level_bounds(hyrsdata: str) -> pd.DataFrame:
    """HYRSDATA's HYRSMINVOL and HYRSMAXVOL by (Area, Bound) x season."""
    rows, _ = table_rows(hyrsdata.splitlines(), "HYRSDATA", GKFX_ROW,
                         lambda m: m.group(2).upper() in ("HYRSMINVOL", "HYRSMAXVOL"))
    return pd.DataFrame({(m.group(1), m.group(2).upper()): {s: float(v) for s, v in values.items()}
                         for _, m, values in rows}).T.sort_index(axis=1)


def compare(volume: pd.Series, bounds: pd.DataFrame, area_regions: dict[str, str],
            path: Path, year: int, seasonal: bool = False) -> pd.DataFrame:
    """Per region: Balmorel volume, highest reachable level, observed max and
    min, whether the HYRSDATA envelope is seasonal, the factor that brings
    the reachable level down to the observed maximum (Factor_obs, 1 where it
    is already below), the Factor applied (Factor_obs, or 1 for seasonal
    envelopes unless `seasonal`), and the weeks of the observed trajectory
    outside the envelope scaled by Factor."""
    rows = []
    areas = volume[volume > 0]
    for region, group in areas.groupby(lambda a: area_regions.get(a, a)):
        upper = bounds.xs("HYRSMAXVOL", level=1).reindex(group.index)
        lower = bounds.xs("HYRSMINVOL", level=1).reindex(group.index)
        bounded = upper.notna().any(axis=1).all()
        varies = bool((upper.nunique(axis=1) > 1).any() or (lower.nunique(axis=1) > 1).any())
        top = upper.mul(group, axis=0).sum().max() if bounded else float("nan")
        code = entsoe_code(region)
        obs = observed_filling(path, year, code)
        row = dict(Region=region, Areas=" ".join(group.index), Code=code,
                   Volume_GWh=group.sum() / 1e3, Reachable_GWh=top / 1e3,
                   Observed_max_GWh=obs.max() / 1e3 if obs is not None else float("nan"),
                   Observed_min_GWh=obs.min() / 1e3 if obs is not None else float("nan"),
                   Seasonal=varies)
        row["Factor_obs"] = obs.max() / top if obs is not None and bounded and top > obs.max() else 1.0
        factor = row["Factor"] = row["Factor_obs"] if seasonal or not varies else 1.0
        if obs is not None and bounded:
            # Observed weeks against the scaled envelope of the same season
            season = obs.index.isocalendar().week.clip(upper=52).map(lambda w: f"S{w:02d}")
            hi = upper.mul(group, axis=0).sum().reindex(season).values * factor
            lo = lower.mul(group, axis=0).sum().reindex(season).values * factor
            row["Weeks_above"] = int((obs.values > hi * 1.001).sum())
            row["Weeks_below"] = int((obs.values < lo * 0.999).sum())
        rows.append(row)
    return pd.DataFrame(rows).set_index("Region")


def write_override(table: pd.DataFrame, path: Path, year: int, command: str) -> None:
    """A HYRSMAXVOL_G.inc that includes base's and scales the cut regions."""
    cut = table[table.Factor < 1]
    lines = [
        f"* Reservoir volumes cut to the ENTSO-E observed maximum filling of {year} (16.1.D):",
        "* where the highest level Balmorel can reach (max over seasons of HYRSDATA's",
        "* HYRSMAXVOL x volume) is above it, HYRSMAXVOL_G is scaled so they are equal.",
        "* Regions below the observed maximum, or without ENTSO-E data, keep base's.",
        *(["* Regions with a seasonal HYRSDATA envelope (the Nordics) are cut too (--seasonal)."]
          if (table.Seasonal & (table.Factor < 1)).any() else
          ["* Regions with a seasonal HYRSDATA envelope (the Nordics) keep base's: the envelope",
           "* already holds their historical weekly levels."]),
        f"* Written by: {command}",
        f"$include '{BASE_INCLUDE}';",
        "",
    ]
    for region, row in cut.iterrows():
        lines.append(f"* {region}: volume {row.Volume_GWh:.0f} -> {row.Volume_GWh * row.Factor:.0f} GWh, "
                     f"reachable {row.Reachable_GWh:.0f} -> {row.Observed_max_GWh:.0f} GWh (observed max)")
        lines += [f"HYRSMAXVOL_G('{area}',GGG) = {row.Factor:.6f} * HYRSMAXVOL_G('{area}',GGG);"
                  for area in row.Areas.split()]
    path.write_text("\n".join(lines) + "\n")


@click.command()
@click.argument("year", type=int)
@click.option("--entsoe-path", default="backcast/entsoedata", show_default=True,
              help="Folder of the ENTSO-E csv's; missing ones are downloaded into it")
@click.option("--gkfx", default="base/data/GKFX.inc", show_default=True)
@click.option("--hyrsmaxvol", default="base/data/HYRSMAXVOL_G.inc", show_default=True,
              help=f"Must be the file the output includes ({BASE_INCLUDE})")
@click.option("--hyrsdata", default="base/data/HYRSDATA.inc", show_default=True)
@click.option("--rrraaa", default="base/data/RRRAAA.inc", show_default=True)
@click.option("--capacity-year", type=int, default=None,
              help="GKFX year of the capacities [default: YEAR]")
@click.option("--output", default="backcast/data/HYRSMAXVOL_G.inc", show_default=True)
@click.option("--no-download", is_flag=True, help="Use only the csv's already in --entsoe-path")
@click.option("--seasonal", is_flag=True,
              help="Also cut regions with a seasonal HYRSDATA envelope (the Nordics)")
def main(year, entsoe_path, gkfx, hyrsmaxvol, hyrsdata, rrraaa, capacity_year, output,
         no_download, seasonal):
    entsoe_path = Path(entsoe_path)
    volume = reservoir_volumes(Path(gkfx).read_text(), Path(hyrsmaxvol).read_text(),
                               capacity_year or year)
    area_regions = read_area_regions(Path(rrraaa))

    if not no_download:
        codes = sorted({entsoe_code(area_regions.get(a, a)) for a in volume[volume > 0].index})
        no_data = read_no_data_zones(entsoe_path, year, QUERY)
        missing = [c for c in codes
                   if c not in no_data and not (entsoe_path / f"{year}_{c}_{QUERY}.csv").exists()]
        if missing:
            print(f"Downloading {year} reservoir filling for {', '.join(missing)}")
            fetch_annual_data(QUERY, year, missing, entsoe_path, get_api_key())

    table = compare(volume, level_bounds(Path(hyrsdata).read_text()), area_regions,
                    entsoe_path, year, seasonal)
    command = "pixi run python analysis/hydro_reservoir_volumes.py " + " ".join(sys.argv[1:])
    write_override(table, Path(output), year, command)
    with pd.option_context("display.width", 250, "display.max_rows", 100,
                           "display.max_columns", None, "display.float_format", "{:.2f}".format):
        print(f"Reservoir volume vs ENTSO-E {year} filling (GWh); Factor < 1 is cut:")
        print(table.sort_values("Volume_GWh", ascending=False))
    print("\nsaved", output)


if __name__ == "__main__":
    main()
