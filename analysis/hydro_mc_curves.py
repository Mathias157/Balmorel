"""Hydro marginal cost curves from ENTSO-E data.

Estimates the supply curve of reservoir hydro per bidding zone from one
year of ENTSO-E hourly generation and day-ahead prices. Writes it as the VOM
of the GNR_RES_WTR_NOPMP_MC-01..10 steps, the steps that give Balmorel's
Nordic reservoir hydro its slope.

Method
------
Within a week the water value is roughly constant. Around it, a reservoir
producer offers more water at higher prices, so within a week hydro output
and price rise together along the producer's bid curve. Per zone:

1. Hydro is 'Hydro Water Reservoir' where ENTSO-E reports it, else 'Hydro
   Run-of-river and pondage' (FI reports its regulated hydro there). Pumped
   storage is left out. Hours without hydro or price are dropped.
2. Utilisation u = hydro / K, where K is the 99.9th percentile of hourly
   output.
3. Within each week (Monday to Sunday, Brussels time), the hours' hydro
   outputs are paired with the prices by rank: the i-th lowest output with
   the i-th lowest price (comonotone pairing). If output rises with price,
   this gives the bid curve the week's hours trace out. It does so without
   the noise of hours in which something else (wind, cables, outages) moved
   the price. Where that assumption is weak, the pairing makes the curve
   steeper, hence the quality gate in 6.
4. Price is regressed on week fixed effects plus dummies for N equal bands
   of u. A band's coefficient is its price premium over the lowest band in
   the same week; the week effects absorb the water value. Bands with fewer
   than --min-hours hours are left out.
5. The band premia are made non-decreasing by isotonic regression, weighted
   by hours. Bands that were left out are then filled: linearly between
   estimated bands, flat beyond them (no slope without data).
6. A zone passes if all three hold:
   - K >= --min-capacity;
   - the median within-week rank correlation of hydro and price is
     >= --min-rank-corr;
   - at least 3 bands are estimated.

The curve (nominal EUR/MWh above the lowest band) is converted to EUR2016
with the euro-area HICP deflator of the year.

Balmorel
--------
The Nordic areas model reservoir hydro as 10 equal capacity steps:
GNR_RES_WTR_NOPMP_MC-01..10, where GNR_RES_WTR_PMP_MC-01 (if any) is part
of step 1. All steps share the area's reservoir and inflow, and each has
its own VOM.

Elsewhere, reservoir hydro is a single GNR_RES_WTR_NOPMP with VOM 0. AT and
IT also have capacity in GNR_RES_WTR_PMP_MC-01. Such an area can't take a
curve. Unless --no-split is given, these areas are split the Nordic way:
- GKFX: their GNR_RES_WTR_NOPMP and GNR_RES_WTR_PMP_MC-01 rows become 10
  equal GNR_RES_WTR_NOPMP_MC rows, each holding a tenth of the sum in every
  year.
- HYRSMAXVOL_G: the MC step columns get the area's GNR_RES_WTR_NOPMP value,
  so every MW of reservoir hydro gets the same storage per MW, as in the
  Nordic areas. The GNR_RES_WTR_NOPMP column stays for scenarios with their
  own unsplit GKFX.
Totals and inflows (WTRRSFLH is per area) are unchanged. The volume does
change where GNR_RES_WTR_PMP_MC-01 had no HYRSMAXVOL_G entry: AT goes from
0 (no seasonal storage) to 276 MWh/MW, and IT's PMP_MC-01 capacity gets
storage. Areas without a GNR_RES_WTR_NOPMP entry (e.g. LV) keep zero
volume.

Each area with MC steps gets the curve of its region's zone. Where the
region has several zones (IT), it gets the zone with the most hydro (K).
Step k covers the k-th slice of the area's step capacity: the cumulative
capacity up to step k, as a fraction of the total. Its VOM is --lowest-vom
(the VOM of step 1), plus the curve's mean premium over step k's slice,
minus the mean premium over step 1's slice.

Areas whose zone fails the gate or has no data (e.g. TR) get the median of
the passing zones' curves.

The VOMs are written as GOMVCOSTO assignments, which override GDATA's
GDOMVCOST0 per area. Balmorel replaces a zero GOMVCOSTO with the GDATA
default, so a zero is written as EPS.

The year is a weather-year choice: the bids follow that year's water and
prices. In a backcast of the same year, the within-week price-vs-hydro
slope (analysis/backcast_hydro_slope.py) is then in-sample. Monthly prices,
duration curves, capture rates and flows are still out of sample.

Portability
-----------
Sections 1 and 2 depend only on pybalmorel.entsoe and the deflator. They
are meant to move to pybalmorel.entsoe (e.g. entsoe/hydrocurves.py).
Section 3 is the Balmorel-specific part (GAMS table reading, the split and
the writer).

Future (maybe): analysis/hydro_reservoir_volumes.py cuts reservoir volumes
to the year's ENTSO-E maximum filling (16.1.D). It uses this script's table
readers and takes the same year and zones. With this script, it could form
one year-aligned hydro step (curves + volumes) when both move to
pybalmorel.entsoe. The volume cut is year-specific (a dry year's maximum
underestimates the volume), so it belongs with the backcast. The curves
are in base.

Run from the repo root:
    pixi run python analysis/hydro_mc_curves.py 2023
Then copy the written files into base/data, or into a scenario's data folder
to override base's for that scenario:
- GOMVCOSTO.inc, always;
- GKFX.inc and HYRSMAXVOL_G.inc, if any area was split. These are copies of
  the input files, with only the split areas' rows changed. Once they're in
  place, a rerun finds nothing to split and writes only GOMVCOSTO.inc.
"""

import re
import sys
from pathlib import Path

import click
import numpy as np
import pandas as pd
from pybalmorel.backcasting.pricelevel import PRICE_YEAR, deflator
from pybalmorel.entsoe import (
    bidding_zone_translation,
    bidding_zones,
    entsoe_subzones,
    fetch_annual_data,
    get_api_key,
    read_no_data_zones,
    region_to_entsoe_code,
    zone_eic_code,
    zone_to_region,
)
from pybalmorel.entsoe.profile import _read_generation_csv, _read_series_csv, _zone_files

RESERVOIR = "Hydro Water Reservoir"
# Second spelling is from older entsoe-py versions
PONDAGE = ("Hydro Run-of-river and pondage", "Hydro Run-of-river and poundage")
QUERIES = ("generation", "day_ahead_prices")
TIME_ZONE = "Europe/Brussels"
MC_STEP = re.compile(r"^GNR_RES_WTR_NOPMP_MC-(\d+)$")
STEP = "GNR_RES_WTR_NOPMP_MC-{:02d}"
SINGLE = "GNR_RES_WTR_NOPMP"  # unsplit reservoir hydro, VOM 0
PUMPED = "GNR_RES_WTR_PMP_MC-01"  # part of step 1 (it's GHYRS, it doesn't pump)
STEPS = 10
GKFX_ROW = re.compile(r"^\s*(\S+)\s+\.\s+(\S+)")


def is_reservoir(match: re.Match) -> bool:
    """Whether a GKFX row (match of GKFX_ROW) is reservoir hydro."""
    return match.group(2) in (SINGLE, PUMPED) or bool(MC_STEP.match(match.group(2)))
AREA_ROW = re.compile(r"^\s*([^\s*;]\S*)")


# ------------------------------- #
#     1. ENTSO-E data (portable)  #
# ------------------------------- #


def fetch_missing(path: Path, year: int, zones: list[str]) -> None:
    """Download the generation and day-ahead price csv's of `zones` that are
    neither in `path` nor on its no-data list. Asks for the API key only if
    something is missing."""
    missing = {}
    for query in QUERIES:
        files = _zone_files(path, year, query)
        no_data = read_no_data_zones(path, year, query)
        missing[query] = [
            region_to_entsoe_code(zone)
            for zone in zones
            if zone_eic_code(zone) not in files and region_to_entsoe_code(zone) not in no_data
        ]
    if not any(missing.values()):
        return
    api_key = get_api_key()
    path.mkdir(parents=True, exist_ok=True)
    for query, codes in missing.items():
        if codes:
            print(f"Downloading {year} {query} for {', '.join(codes)}")
            fetch_annual_data(query, year, codes, path, api_key)


def hydro_and_price(path: Path, year: int, zone: str) -> tuple[pd.DataFrame | None, str]:
    """Hourly hydro output (MW, column 'h') and day-ahead price (nominal
    EUR/MWh, column 'p') of `zone`, indexed by UTC time, on the hours that
    have both. Also returns the production type used as hydro: reservoir
    where reported, else run-of-river and pondage. Returns (None, reason)
    without data."""
    eic = zone_eic_code(zone)
    generation = _zone_files(path, year, "generation").get(eic)
    prices = _zone_files(path, year, "day_ahead_prices").get(eic)
    if generation is None or prices is None:
        return None, "no generation or price file"

    g = _read_generation_csv(generation)
    if RESERVOIR in g:
        kind, hydro = "reservoir", g[RESERVOIR]
    elif pondage := [c for c in PONDAGE if c in g]:
        kind, hydro = "pondage", g[pondage].sum(axis=1, min_count=1)
    else:
        return None, "no reservoir or pondage hydro"
    df = pd.DataFrame({"h": hydro, "p": _read_series_csv(prices).reindex(g.index)}).dropna()
    return (df, kind) if len(df) else (None, "no hours with both")


def week_of(index: pd.DatetimeIndex) -> np.ndarray:
    """Monday-start week (its first day, local time) of each UTC hour."""
    local = index.tz_convert(TIME_ZONE).tz_localize(None)
    return local.to_period("W-SUN").start_time.values


# ------------------------------- #
#   2. Supply curve (portable)    #
# ------------------------------- #


def comonotone(h: pd.Series, p: pd.Series, week: np.ndarray) -> pd.Series:
    """Hydro outputs re-paired with prices by rank within each week: each
    hour gets the output of the same rank in the week as its price."""
    paired = pd.Series(np.nan, index=h.index)
    for _, hours in pd.Series(np.arange(len(h))).groupby(week).groups.items():
        hours = np.asarray(hours)
        order = np.argsort(p.values[hours], kind="stable")
        paired.iloc[hours[order]] = np.sort(h.values[hours])
    return paired


def band_premia(p: pd.Series, band: pd.Series, week: np.ndarray, bands: int,
                min_hours: int) -> tuple[pd.Series, pd.Series]:
    """Price premium of each utilisation band over the lowest estimated band,
    with week fixed effects, and the hours per band. Bands with fewer than
    `min_hours` hours are NaN; their hours are left out."""
    hours = band.value_counts().reindex(range(bands), fill_value=0)
    estimated = hours.index[hours >= min_hours]
    premia = pd.Series(np.nan, index=range(bands))
    if len(estimated) == 0:
        return premia, hours
    premia[estimated[0]] = 0.0
    if len(estimated) == 1:
        return premia, hours

    keep = band.isin(estimated).values
    p, band, week = p[keep], band[keep], week[keep]
    dummies = pd.get_dummies(band).reindex(columns=estimated[1:], fill_value=0).astype(float)
    x = dummies - dummies.groupby(week).transform("mean")
    y = p - p.groupby(week).transform("mean")
    coef, *_ = np.linalg.lstsq(x.values, y.values, rcond=None)
    premia[estimated[1:]] = coef
    return premia, hours


def isotonic(y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Weighted least-squares non-decreasing fit (pool adjacent violators)."""
    blocks = []  # [mean, weight, count]
    for yi, wi in zip(y, w):
        blocks.append([yi, wi, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            m2, w2, n2 = blocks.pop()
            m1, w1, n1 = blocks.pop()
            blocks.append([(m1 * w1 + m2 * w2) / (w1 + w2), w1 + w2, n1 + n2])
    return np.repeat([b[0] for b in blocks], [b[2] for b in blocks])


def smooth(premia: pd.Series, hours: pd.Series) -> pd.Series:
    """Non-decreasing curve over all bands, starting at 0: isotonic over the
    estimated bands, linear between them, flat beyond them."""
    estimated = premia.dropna()
    curve = pd.Series(np.nan, index=premia.index)
    curve[estimated.index] = isotonic(estimated.values, hours[estimated.index].values)
    curve = curve.interpolate(limit_area="inside").ffill().bfill()
    return curve - curve.iloc[0]


def mean_step(premia: pd.Series) -> float:
    """Mean premium per band between the lowest and highest estimated band."""
    estimated = premia.dropna()
    if len(estimated) < 2:
        return np.nan
    return (estimated.iloc[-1] - estimated.iloc[0]) / (estimated.index[-1] - estimated.index[0])


def supply_curve(df: pd.DataFrame, bands: int, min_hours: int,
                 quantile: float = 0.999) -> tuple[pd.Series, dict]:
    """The hydro supply curve of one zone, in nominal EUR/MWh above the
    lowest of `bands` equal utilisation bands, and its diagnostics."""
    week = week_of(df.index)
    capacity = df.h.quantile(quantile)
    rank_corr = df.groupby(week).apply(lambda w: w.h.corr(w.p, method="spearman")).median()

    def band_of(h):
        return np.clip((h / capacity * bands).astype(int), 0, bands - 1)

    paired = comonotone(df.h, df.p, week)
    premia, hours = band_premia(df.p, band_of(paired), week, bands, min_hours)
    raw, _ = band_premia(df.p, band_of(df.h), week, bands, min_hours)
    curve = smooth(premia, hours)
    return curve, {
        "capacity_MW": capacity,
        "hours": len(df),
        "weeks": len(np.unique(week)),
        "rank_corr": rank_corr,
        "u_p01": (df.h / capacity).quantile(0.01),
        "u_median": (df.h / capacity).median(),
        "bands_estimated": int(premia.notna().sum()),
        "step_comonotone": mean_step(premia),
        "step_raw": mean_step(raw),
        "spread": curve.iloc[-1],
        "hours_per_band": " ".join(str(h) for h in hours.values),
    }


def hydro_curves(path: Path, year: int, zones: list[str], bands: int = 10,
                 min_hours: int = 50, min_capacity: float = 200.0,
                 min_rank_corr: float = 0.5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hydro supply curves of `zones` from the ENTSO-E data of `year`.

    Returns:
        - the curves in EUR2016/MWh above the lowest band, one row per zone
          and one column per band (0 = lowest utilisation);
        - per zone, its diagnostics and whether it passes the quality gate.
          Diagnostic prices are nominal EUR/MWh.
    """
    to_2016 = deflator(year)
    curves, diagnostics = {}, {}
    for zone in zones:
        df, kind = hydro_and_price(path, year, zone)
        if df is None:
            diagnostics[zone] = {"hydro": None, "passes": False, "reason": kind}
            continue
        if (capacity := df.h.quantile(0.999)) < min_capacity:
            diagnostics[zone] = {"hydro": kind, "capacity_MW": capacity, "passes": False,
                                 "reason": f"K < {min_capacity:g} MW"}
            continue
        curve, row = supply_curve(df, bands, min_hours)
        reasons = [
            reason
            for failed, reason in [
                (not row["rank_corr"] >= min_rank_corr, f"rank corr < {min_rank_corr:g}"),
                (row["bands_estimated"] < 3, "< 3 bands"),
            ]
            if failed
        ]
        diagnostics[zone] = {"hydro": kind, **row, "passes": not reasons,
                             "reason": "; ".join(reasons)}
        curves[zone] = curve * to_2016
    curves = pd.DataFrame(curves).T.rename_axis("Zone")
    curves.columns.name = "Band"
    return curves, pd.DataFrame(diagnostics).T.rename_axis("Zone")


# ------------------------------- #
#     3. Balmorel (MC steps)      #
# ------------------------------- #


Columns = list[tuple[int, int, str]]


def table_header(lines: list[str], name: str) -> tuple[int, Columns]:
    """Line index of the column header of GAMS table `name`, and its columns
    as (start, end, name) character spans."""
    start = next(i for i, line in enumerate(lines)
                 if re.match(rf"^\s*TABLE\s+{re.escape(name)}\s*\(", line, flags=re.I))
    head = next(i for i in range(start + 1, len(lines))
                if lines[i].strip() and not lines[i].startswith("*"))
    text = lines[head].split("/*")[0]
    return head, [(m.start(), m.end(), m.group()) for m in re.finditer(r"\S+", text)]


def row_values(line: str, label_end: int, columns: Columns) -> dict[str, str]:
    """The numbers of a table row by column. As GAMS reads a table, a number
    belongs to the column whose header it overlaps."""
    values = {}
    for number in re.finditer(r"\S+", line[label_end:]):
        s, e = number.start() + label_end, number.end() + label_end
        hits = [column for cs, ce, column in columns if s < ce and e > cs]
        if len(hits) != 1:
            raise ValueError(f"'{number.group()}' is under {len(hits)} columns in: {line.strip()[:80]}")
        values[hits[0]] = number.group()
    return values


def format_row(label: str, values: dict[str, str], columns: Columns) -> str:
    """A table row with each value starting where its column header starts,
    the layout of Balmorel's tables."""
    line = label
    for start, _, column in columns:
        if column in values:
            if len(line) >= start:
                raise ValueError(f"No room for {column} in: {line.strip()[:80]}")
            line = line.ljust(start) + values[column]
    if row_values(line, len(label), columns) != values:
        raise ValueError(f"Values don't fit their columns in: {line.strip()[:80]}")
    return line


def table_rows(lines: list[str], name: str, label: re.Pattern, keep=lambda match: True):
    """(line index, label match, values by column) of the data rows of GAMS
    table `name` whose label match passes `keep`, up to the ';' that ends
    the table, and the table's columns."""
    head, columns = table_header(lines, name)
    rows = []
    for i in range(head + 1, len(lines)):
        if lines[i].lstrip().startswith(";"):
            break
        if lines[i].startswith("*") or not (match := label.match(lines[i])) or not keep(match):
            continue
        rows.append((i, match, row_values(lines[i], match.end(), columns)))
    return rows, columns


def reservoir_capacities(gkfx: str) -> pd.DataFrame:
    """Area, Technology, Year and Capacity (MW) of the reservoir hydro rows
    (GNR_RES_WTR_NOPMP, GNR_RES_WTR_PMP_MC-01 and the MC steps) of the GKFX1
    table of a GKFX.inc's text."""
    rows, _ = table_rows(gkfx.splitlines(), "GKFX1", GKFX_ROW, is_reservoir)
    return pd.DataFrame(
        [(m.group(1), m.group(2), int(year), float(value))
         for _, m, values in rows for year, value in values.items()],
        columns=["Area", "Technology", "Year", "Capacity"])


def storage_per_mw(hyrsmaxvol: str) -> pd.Series:
    """HYRSMAXVOL_G (MWh per MW) by (Area, Technology), from the text of a
    HYRSMAXVOL_G.inc."""
    rows, _ = table_rows(hyrsmaxvol.splitlines(), "HYRSMAXVOL_G", AREA_ROW)
    return pd.Series({(m.group(1), tech): float(value)
                      for _, m, values in rows for tech, value in values.items()},
                     dtype=float).rename_axis(["Area", "Technology"])


def reservoir_volumes(gkfx: str, hyrsmaxvol: str, year: int) -> pd.Series:
    """Reservoir volume (MWh) per area in `year`: the sum over its reservoir
    hydro of capacity times HYRSMAXVOL_G, as in Balmorel's QHYRSMAXVOL."""
    capacity = reservoir_capacities(gkfx)
    capacity = capacity[capacity.Year == year].set_index(["Area", "Technology"])
    per_mw = storage_per_mw(hyrsmaxvol).reindex(capacity.index).fillna(0)
    return (capacity.Capacity * per_mw).groupby("Area").sum()


def split_reservoirs(gkfx: str, hyrsmaxvol: str, steps: int = STEPS) -> tuple[str, str, list[str]]:
    """Split the reservoir hydro of every area without MC steps into `steps`
    equal MC steps, as the Nordic areas'. Returns the new texts of GKFX.inc
    and HYRSMAXVOL_G.inc, and the split areas. See the module docstring."""
    def fmt(x):
        return f"{x:.10g}"

    newline = "\r\n" if "\r\n" in gkfx else "\n"
    lines = gkfx.splitlines()
    rows, columns = table_rows(lines, "GKFX1", GKFX_ROW, is_reservoir)
    reservoirs = {}  # area -> [(line index, label match, values)]
    for i, match, values in rows:
        reservoirs.setdefault(match.group(1), []).append((i, match, values))
    areas = [area for area, area_rows in reservoirs.items()
             if not any(MC_STEP.match(m.group(2)) for _, m, _ in area_rows)]

    replace = {}
    for area in areas:
        total = {}
        for _, _, values in reservoirs[area]:
            for year, value in values.items():
                total[year] = total.get(year, 0.0) + float(value)
        first, match, _ = reservoirs[area][0]
        technologies = " + ".join(m.group(2) for _, m, _ in reservoirs[area])
        label = lines[first][:match.start(2)]
        replace[first] = [f"* {area}: {technologies} split into {steps} equal MC steps "
                          "by analysis/hydro_mc_curves.py"] + [
            format_row(label + STEP.format(k), {y: fmt(t / steps) for y, t in total.items()},
                       columns)
            for k in range(1, steps + 1)]
        for i, _, _ in reservoirs[area][1:]:
            replace[i] = []
    gkfx = newline.join(new for i, line in enumerate(lines)
                        for new in replace.get(i, [line])) + newline

    newline = "\r\n" if "\r\n" in hyrsmaxvol else "\n"
    lines = hyrsmaxvol.splitlines()
    rows, columns = table_rows(lines, "HYRSMAXVOL_G", AREA_ROW)
    if missing := [STEP.format(k) for k in range(1, steps + 1)
                   if STEP.format(k) not in {c for _, _, c in columns}]:
        raise ValueError(f"HYRSMAXVOL_G has no column for {', '.join(missing)}")
    for i, match, values in rows:
        if match.group(1) in areas and SINGLE in values:
            values |= {STEP.format(k): values[SINGLE] for k in range(1, steps + 1)}
            lines[i] = format_row(lines[i][:match.end()], values, columns).rstrip()
    end = next(i for i in range(rows[-1][0], len(lines)) if lines[i].lstrip().startswith(";"))
    lines[end + 1:end + 1] = [
        "* The MC step columns of the areas whose reservoir hydro",
        "* analysis/hydro_mc_curves.py split into MC steps (see GKFX.inc) are copies of",
        "* their GNR_RES_WTR_NOPMP column, which stays for unsplit GKFX's:",
        *("* " + " ".join(areas[i:i + 10]) for i in range(0, len(areas), 10)),
    ]
    return gkfx, newline.join(lines) + newline, areas


def read_mc_steps(gkfx: str, year: int) -> pd.DataFrame:
    """Area, Technology, Step and Capacity (MW, in `year`) of the MC steps of
    the areas that have them, from the text of a GKFX.inc.
    GNR_RES_WTR_PMP_MC-01 counts as part of step 1."""
    capacity = reservoir_capacities(gkfx)
    if year not in capacity.Year.values:
        raise click.UsageError(f"GKFX has no {year} column")
    stepped = capacity.Area[capacity.Technology.str.match(MC_STEP)].unique()
    steps = (capacity[capacity.Area.isin(stepped) & (capacity.Technology != SINGLE)]
             .pivot_table(index=["Area", "Technology"], columns="Year", values="Capacity")
             .reindex(columns=[year]).fillna(0)[year].rename("Capacity").reset_index())
    steps.insert(2, "Step", [int(m.group(1)) if (m := MC_STEP.match(t)) else 1
                             for t in steps.Technology])
    return steps


def read_area_regions(rrraaa_path: Path) -> dict[str, str]:
    """Area -> region from the 'region . area' lines of RRRAAA.inc."""
    pairs = re.findall(r"^\s*(\S+)\s+\.\s+(\S+)", rrraaa_path.read_text(), flags=re.M)
    return {area: region for region, area in pairs if not region.startswith("*")}


def step_voms(curve: pd.Series, capacities: pd.Series, lowest_vom: float) -> pd.Series:
    """VOM (EUR2016/MWh) of each step: the curve's mean over the step's slice
    of cumulative capacity, relative to step 1's, on top of `lowest_vom`.
    Without capacity, the slices are equal."""
    if capacities.sum() > 0:
        edges = np.r_[0, capacities.cumsum().values] / capacities.sum()
    else:
        edges = np.linspace(0, 1, len(capacities) + 1)
    bands = len(curve)
    band_edges = np.arange(bands + 1) / bands

    def mean_over(a, b):
        overlap = np.clip(np.minimum(b, band_edges[1:]) - np.maximum(a, band_edges[:-1]), 0, None)
        return (curve.values * overlap).sum() / (b - a)

    means = np.array([mean_over(a, b) for a, b in zip(edges[:-1], edges[1:])])
    return pd.Series(lowest_vom + means - means[0], index=capacities.index)


def curve_zone(region: str, diagnostics: pd.DataFrame) -> str:
    """The zone whose curve a Balmorel region gets: of the ENTSO-E zones that
    make up the region, the one with the most hydro (K)."""
    zones = entsoe_subzones(bidding_zone_translation.get(region, region))
    capacity = pd.to_numeric(diagnostics.capacity_MW, errors="coerce").reindex(zones).fillna(0)
    return capacity.idxmax()


def balmorel_steps(curves: pd.DataFrame, diagnostics: pd.DataFrame, steps: pd.DataFrame,
                   area_regions: dict[str, str], lowest_vom: float) -> tuple[pd.DataFrame, pd.Series]:
    """VOM of every MC step, from its area's zone curve, or from the median
    curve of the passing zones where that zone fails or has no data. Also
    returns the median curve."""
    passing = diagnostics.index[diagnostics.passes.astype(bool)]
    median = curves.loc[curves.index.intersection(passing)].median()
    out = []
    for area, area_steps in steps.sort_values(["Area", "Step", "Technology"]).groupby("Area"):
        region = area_regions.get(area, area)
        zone = curve_zone(region, diagnostics)
        source = zone if zone in passing else "median"
        curve = curves.loc[zone] if source == zone else median
        voms = step_voms(curve, area_steps.groupby("Step").Capacity.sum(), lowest_vom)
        out.append(area_steps.assign(Region=region, Zone=zone, Curve=source,
                                     VOM=area_steps.Step.map(voms).values))
    return pd.concat(out, ignore_index=True), median


def write_gomvcosto(steps: pd.DataFrame, path: Path, year: int, command: str) -> None:
    """GOMVCOSTO assignments of the MC step VOMs, a zero written as EPS."""
    lines = [
        "* GENERATED by analysis/hydro_mc_curves.py - do not edit by hand, rerun it:",
        f"*   {command}",
        f"* Reservoir hydro marginal cost steps (EUR{PRICE_YEAR}/MWh), estimated from",
        f"* ENTSO-E {year} hourly hydro generation and day-ahead prices. Overrides",
        "* GDATA(G,'GDOMVCOST0') of GNR_RES_WTR_NOPMP_MC-* per area, and of",
        "* GNR_RES_WTR_PMP_MC-01, which is part of step 1.",
        "* Used as base/data/GOMVCOSTO.inc, or as a scenario's data/GOMVCOSTO.inc,",
        "* which replaces base's entirely.",
        "",
    ]
    for area, rows in steps.groupby("Area", sort=False):
        source = rows.Curve.iloc[0]
        note = f"zone {source}" if source != "median" else \
            f"median of the passing zones ({rows.Zone.iloc[0]} fails or has no data)"
        lines.append(f"* {area} ({rows.Region.iloc[0]}): {note}")
        for row in rows.itertuples():
            value = "EPS" if row.VOM == 0 else f"{row.VOM:.2f}"
            lines.append(f"GOMVCOSTO('{area}','{row.Technology}') = {value};")
        lines.append("")
    path.write_text("\n".join(lines))


@click.command()
@click.argument("year", type=int)
@click.option("--entsoe-path", default="backcast/entsoedata", show_default=True,
              help="Folder of the ENTSO-E csv's; missing ones are downloaded into it")
@click.option("--zones", default=None,
              help="Comma-separated zones as Balmorel region names, e.g. NO2,SE3,FI "
              "[default: all pybalmorel bidding zones]")
@click.option("--bands", default=10, show_default=True, help="Utilisation bands of the curve")
@click.option("--min-hours", default=50, show_default=True,
              help="Hours a band needs to be estimated")
@click.option("--min-capacity", default=200.0, show_default=True,
              help="Hydro capacity K (MW) a zone needs to pass")
@click.option("--min-rank-corr", default=0.5, show_default=True,
              help="Median within-week rank correlation a zone needs to pass")
@click.option("--lowest-vom", default=1.0, show_default=True,
              help=f"VOM of step 1 (EUR{PRICE_YEAR}/MWh), the curve's anchor")
@click.option("--gkfx", default="base/data/GKFX.inc", show_default=True,
              help="GKFX.inc holding the reservoir hydro capacities (TABLE GKFX1)")
@click.option("--hyrsmaxvol", default="base/data/HYRSMAXVOL_G.inc", show_default=True,
              help="HYRSMAXVOL_G.inc to add the split areas' MC step columns to")
@click.option("--split/--no-split", default=True, show_default=True,
              help="Split the reservoir hydro of areas without MC steps into MC steps")
@click.option("--rrraaa", default="base/data/RRRAAA.inc", show_default=True)
@click.option("--capacity-year", type=int, default=None,
              help="GKFX year of the step capacities [default: YEAR]")
@click.option("--output-path", default="analysis/output/hydro_mc", show_default=True)
@click.option("--no-download", is_flag=True, help="Use only the csv's already in --entsoe-path")
def main(year, entsoe_path, zones, bands, min_hours, min_capacity, min_rank_corr, lowest_vom,
         gkfx, hyrsmaxvol, split, rrraaa, capacity_year, output_path, no_download):
    entsoe_path = Path(entsoe_path)
    zones = zones.split(",") if zones else list(dict.fromkeys(zone_to_region(z) for z in bidding_zones))
    if not no_download:
        fetch_missing(entsoe_path, year, zones)

    curves, diagnostics = hydro_curves(entsoe_path, year, zones, bands, min_hours,
                                       min_capacity, min_rank_corr)
    output_path = Path(output_path) / str(year)
    output_path.mkdir(parents=True, exist_ok=True)
    capacity_year = capacity_year or year
    area_regions = read_area_regions(Path(rrraaa))

    gkfx_text, hyrsmaxvol_text = Path(gkfx).read_text(), Path(hyrsmaxvol).read_text()
    split_areas = []
    if split:
        new_gkfx, new_hyrsmaxvol, split_areas = split_reservoirs(gkfx_text, hyrsmaxvol_text)
    saved = ["curves.csv", "diagnostics.csv", "steps.csv", "GOMVCOSTO.inc"]
    if split_areas:
        before = reservoir_volumes(gkfx_text, hyrsmaxvol_text, capacity_year)
        after = reservoir_volumes(new_gkfx, new_hyrsmaxvol, capacity_year)
        capacity = reservoir_capacities(new_gkfx)
        capacity = capacity[capacity.Year == capacity_year].groupby("Area").Capacity.sum()
        split_table = pd.DataFrame({
            "Region": [area_regions.get(a, a) for a in split_areas],
            "Capacity_MW": capacity.reindex(split_areas).fillna(0).values,
            "Volume_before_GWh": before.reindex(split_areas).fillna(0).values / 1e3,
            "Volume_after_GWh": after.reindex(split_areas).fillna(0).values / 1e3,
        }, index=pd.Index(split_areas, name="Area"))
        (output_path / "GKFX.inc").write_text(new_gkfx)
        (output_path / "HYRSMAXVOL_G.inc").write_text(new_hyrsmaxvol)
        split_table.round(1).to_csv(output_path / "split.csv")
        saved += ["GKFX.inc", "HYRSMAXVOL_G.inc", "split.csv"]
        gkfx_text = new_gkfx
    else:
        for stale in ("GKFX.inc", "HYRSMAXVOL_G.inc", "split.csv"):
            (output_path / stale).unlink(missing_ok=True)

    steps = read_mc_steps(gkfx_text, capacity_year)
    steps, median = balmorel_steps(curves, diagnostics, steps, area_regions, lowest_vom)
    command = "pixi run python analysis/hydro_mc_curves.py " + " ".join(sys.argv[1:])
    curves.loc["median"] = median
    curves.round(3).to_csv(output_path / "curves.csv")
    diagnostics.to_csv(output_path / "diagnostics.csv")
    steps.round(3).to_csv(output_path / "steps.csv", index=False)
    write_gomvcosto(steps, output_path / "GOMVCOSTO.inc", year, command)

    shown = diagnostics[diagnostics.hydro.notna()].drop(columns="hours_per_band")
    with pd.option_context("display.width", 250, "display.max_rows", 100,
                           "display.max_columns", None, "display.float_format", "{:.2f}".format):
        print(f"Hydro supply curves from ENTSO-E {year}, steps in nominal EUR/MWh per band:")
        print(shown.sort_values("capacity_MW", ascending=False))
        print(f"\nCurves, EUR{PRICE_YEAR}/MWh above the lowest of {bands} utilisation bands:")
        print(curves.loc[[z for z in curves.index if z == "median"
                          or diagnostics.passes.get(z, False)]])
        if split_areas:
            print(f"\nSplit into {STEPS} MC steps ({capacity_year} capacity and reservoir volume):")
            print(split_table)
        else:
            print("\nNo area to split" + ("" if split else " (--no-split)"))
        print(f"\nBalmorel MC step VOMs (EUR{PRICE_YEAR}/MWh):")
        print(steps.pivot_table(index=["Area", "Curve"], columns="Step", values="VOM"))
    print("\nsaved", *(output_path / f for f in saved))


if __name__ == "__main__":
    main()
