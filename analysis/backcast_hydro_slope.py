"""Slope of the hydro supply curve in a backcast, against ENTSO-E.

Measures how much the price moves when hydro output moves, within a week:
per region, price and hydro output are demeaned within each Backcast
Calendar week (Season), then the price deviations are regressed on the hydro
deviations. The slope (€/MWh per GW) is the steepness of the hydro bid curve
around the week's water value. Demeaning per week removes the seasonal water
value, which perfect foresight sets in Balmorel and the market sets in its
own way, so only the short-term response is left.

Used to calibrate GDOMVCOST0 of GNR_RES_WTR_NOPMP_MC-01..10 in
base/data/GDATA.inc, the 10 VOM steps that give the Nordic reservoir hydro
supply curve its slope. To first order the slope scales with the step
spread, so the median ENTSO-E/Balmorel ratio over MC_REGIONS shows how much
to widen or narrow it. Cables and neighbours also flatten the curve, so
recheck after changing it.

Hydro is natural-inflow hydro on both sides: reservoir and run-of-river,
not pumped storage (pybalmorel's 'Hydro' category). Zones are summed per
canonical region, prices averaged over its zones. Both sides use the same
hours: the solved hours of the Balmorel run in which ENTSO-E reports both a
price and hydro output. Balmorel prices are converted from EUR2016 to nominal
EUR of the backcast year, as ENTSO-E's are.

Meant for the hourly rolling run (R); in F only every 7th hour is solved.

Run from the repo root (GAMS_SYSTEM_DIR comes from .env):
    pixi run python analysis/backcast_hydro_slope.py
"""

from pathlib import Path

import click
import numpy as np
import pandas as pd
from pybalmorel.backcasting.__main__ import (
    balmorel_prices_in_year,
    balmorel_to_category,
    entsoe_to_category,
    load_balmorel_data,
    load_observed_generation,
    load_observed_prices,
)
from pybalmorel.backcasting.calendar import backcast_calendar, from_backcast_grid
from pybalmorel.backcasting.flows import canonical_region

# Regions with GNR_RES_WTR_NOPMP_MC-* capacity in base/data
MC_REGIONS = ["NO1", "NO2", "NO3", "NO4", "NO5", "SE1", "SE2", "SE3", "FI"]
SOURCES = {"ENTSOE": "ENTSO-E", "BALMOREL": "Balmorel"}


def balmorel_data(scenario: str, scenario_path: str, year: int, overwrite: bool):
    """Hourly Balmorel hydro output (GW) and price (nominal €/MWh), each
    indexed by 'Time' with one column per canonical region, solved hours only."""
    _, prices, generation, _ = load_balmorel_data(scenario, scenario_path, year, overwrite)
    cached = set(generation.Scenario.unique()) | set(prices.Scenario.unique())
    if cached != {scenario}:
        raise click.UsageError(
            f"{scenario_path}/backcastoutput holds {sorted(cached)}, not {scenario}. "
            "Rerun with --overwrite to read the scenario's MainResults."
        )

    category = (generation.Technology + " - " + generation.Fuel).map(balmorel_to_category)
    hydro = generation[category == "Hydro"].assign(
        Region=lambda df: df.Region.map(canonical_region)
    )
    hydro = from_backcast_grid(
        hydro.groupby(["Region", "Season", "Time"], as_index=False).Value.sum(), year
    ).pivot_table(index="Time", columns="Region", values="Value") / 1e3

    prices = from_backcast_grid(prices[["Region", "Season", "Time", "Value"]], year)
    prices = balmorel_prices_in_year(prices, year).pivot_table(
        index="Time", columns="Region", values="Value"
    )
    # MainResults leaves out zeros: a missing value in a solved hour was 0
    prices = prices.fillna(0).T.groupby(canonical_region).mean().T
    return hydro.reindex(prices.index).fillna(0), prices


def entsoe_data(entsoe_path: str, year: int):
    """Hourly ENTSO-E hydro output (GW, NaN where not reported) and price
    (nominal €/MWh), each indexed by 'Time' with one column per canonical
    region."""
    hydro = {}
    for region, df in load_observed_generation(entsoe_path, year).items():
        columns = [c for c in df.columns if entsoe_to_category.get(c) == "Hydro"]
        if columns:
            hydro[region] = df[columns].sum(axis=1, min_count=1) / 1e3
    prices = load_observed_prices(entsoe_path, year).T.groupby(canonical_region).mean().T
    return pd.DataFrame(hydro), prices


def within_week(price: pd.Series, hydro: pd.Series, week: pd.Series) -> dict:
    """Slope (€/MWh per GW) of price on hydro output after demeaning both per
    week, with the deviations' std and correlation."""
    df = pd.DataFrame({"p": price, "h": hydro, "w": week}).dropna()
    dev = df[["p", "h"]] - df.groupby("w")[["p", "h"]].transform("mean")
    if dev.h.std() == 0:
        return {"slope": np.nan, "hydro_std": 0.0, "price_std": dev.p.std(), "corr": np.nan}
    return {
        "slope": np.polyfit(dev.h, dev.p, 1)[0],
        "hydro_std": dev.h.std(),
        "price_std": dev.p.std(),
        "corr": np.corrcoef(dev.h, dev.p)[0, 1],
    }


def slope_table(b_hydro, b_prices, e_hydro, e_prices, year: int) -> pd.DataFrame:
    """Per region: the within-week slope, hydro and price std and correlation
    on both sides, on the hours both sides have, and the ENTSO-E/Balmorel
    slope ratio."""
    calendar = backcast_calendar(year).set_index("Timestamp").Season
    rows = {}
    for region in sorted(set(b_hydro.columns) & set(e_hydro.columns) & set(e_prices.columns)):
        e_p = e_prices[region].reindex(b_prices.index)
        e_h = e_hydro[region].reindex(b_prices.index)
        hours = b_prices.index[e_p.notna() & e_h.notna()]
        if hours.empty:
            continue
        week = calendar.reindex(hours)
        row = {("hours", ""): len(hours), ("weeks", ""): week.nunique()}
        for source, (p, h) in {
            "ENTSOE": (e_p, e_h),
            "BALMOREL": (b_prices[region], b_hydro[region]),
        }.items():
            for metric, value in within_week(p[hours], h[hours], week).items():
                row[(metric, source)] = value
        rows[region] = row

    table = pd.DataFrame.from_dict(rows, orient="index")
    table.columns = pd.MultiIndex.from_tuples(table.columns)
    table.index.name = "Region"
    table[("ratio", "")] = table[("slope", "ENTSOE")] / table[("slope", "BALMOREL")]
    return table


@click.command()
@click.option("--scenario", default="backcast_R2023", show_default=True,
              help="MainResults_<scenario>.gdx")
@click.option("--scenario-path", default="backcast", show_default=True)
@click.option("--entsoe-path", default="backcast/entsoedata", show_default=True)
@click.option("--year", default=2023, show_default=True)
@click.option("--min-std", default=0.1, show_default=True,
              help="Within-week hydro std (GW) a region needs on both sides to be listed")
@click.option("--overwrite", is_flag=True,
              help="Reread the MainResults GDX, replacing the scenario folder's backcastoutput "
              "cache (which pybalmorel's format command shares)")
@click.option("--output-path", default="analysis/output", show_default=True)
def main(scenario, scenario_path, entsoe_path, year, min_std, overwrite, output_path):
    b_hydro, b_prices = balmorel_data(scenario, scenario_path, year, overwrite)
    e_hydro, e_prices = entsoe_data(entsoe_path, year)
    table = slope_table(b_hydro, b_prices, e_hydro, e_prices, year)

    listed = (table[("hydro_std", "ENTSOE")] >= min_std) & (
        table[("hydro_std", "BALMOREL")] >= min_std
    )
    table = table[listed].sort_values(("hydro_std", "ENTSOE"), ascending=False)

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    flat = table.copy()
    flat.columns = [f"{s}_{m}" if s else m for m, s in flat.columns]
    flat.round(3).to_csv(output_path / f"hydro_slope_{scenario}.csv")

    with pd.option_context("display.width", 250, "display.max_rows", 200,
                           "display.max_columns", None):
        print("Within-week slope of price on hydro output (€/MWh per GW), std of the "
              "within-week deviations (GW, €/MWh), their correlation:")
        print(flat.round(2))
    mc = table.index.intersection(MC_REGIONS)
    print(f"\nMedian ENTSO-E/Balmorel slope ratio over the MC-step regions "
          f"({', '.join(mc)}): {table.loc[mc, ('ratio', '')].median():.2f}")
    print("saved", output_path / f"hydro_slope_{scenario}.csv")


if __name__ == "__main__":
    main()
