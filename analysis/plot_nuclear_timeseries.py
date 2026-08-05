"""
Plot nuclear generation timeseries

Compares nuclear generation (PRO_YCRAGFST, Fuel == NUCLEAR, summed across all
regions) between the backcast_R2024 and backcast_SPR_R2024 scenarios.

Run with: pixi run python analysis/plot_nuclear_timeseries.py
"""

from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import pandas as pd
from decouple import config
from pybalmorel import MainResults

SCENARIOS = ["backcast_R2024", "backcast_SPR_R2024"]
MODEL_PATH = "backcast/model"
YEAR = 2024
# Okabe-Ito colorblind-safe pair
SCENARIO_COLORS = {
    "backcast_R2024": "#0072B2",
    "backcast_SPR_R2024": "#D55E00",
}


def build_time_index(year: int) -> pd.Series:
    """Map Balmorel Season/Time sets (S01-S52, T001-T168) to real hourly datetimes."""

    calendar = (
        pd.date_range(
            f"{year}-01-01 00:00",
            f"{year}-12-31 23:00",
            freq="h",
            tz=ZoneInfo("Europe/Copenhagen"),
        )
        .isocalendar()
        .reset_index()
    )
    # Balmorel's 52 weeks run from the year's first Monday to the last Sunday
    first_monday = calendar.iloc[:168, :].query("day == 1").index[0]
    last_sunday = calendar.query("day == 7").index[-1]
    datetimes = calendar.loc[first_monday:last_sunday, "index"].reset_index(drop=True)

    seasons = [f"S{i:02d}" for i in range(1, 53)]
    times = [f"T{i:03d}" for i in range(1, 169)]
    st_index = pd.MultiIndex.from_product((seasons, times), names=["Season", "Time"])

    return pd.Series(datetimes.values, index=st_index, name="Datetime")


def get_nuclear_timeseries() -> pd.DataFrame:
    """Load PRO_YCRAGFST for both scenarios and sum nuclear generation across regions."""

    results = MainResults(
        [f"MainResults_{sc}.gdx" for sc in SCENARIOS],
        paths=MODEL_PATH,
        scenario_names=SCENARIOS,
        system_directory=config("GAMS_SYSTEM_DIR", None),
    )

    df = results.get_result("PRO_YCRAGFST").query(
        f'Fuel == "NUCLEAR" and Year == "{YEAR}"'
    )

    nuclear = df.pivot_table(
        index=["Season", "Time"],
        columns="Scenario",
        values="Value",
        aggfunc="sum",
    )

    time_index = build_time_index(YEAR)
    nuclear = nuclear.reindex(time_index.index, fill_value=0)
    nuclear.index = pd.Index(time_index.values, name="Datetime")

    return nuclear[SCENARIOS].sort_index()


def plot_nuclear_timeseries(df: pd.DataFrame, out_path: Path):
    fig, ax = plt.subplots(figsize=(12, 4.5))

    for scenario in SCENARIOS:
        ax.plot(
            df.index,
            df[scenario] / 1e3,
            label=scenario,
            color=SCENARIO_COLORS[scenario],
            linewidth=1,
        )

    ax.set_ylabel("Nuclear Generation [GWh]")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.legend(loc="lower center", ncol=2, bbox_to_anchor=(0.5, 1.02), frameon=False)

    fig.savefig(out_path, bbox_inches="tight", dpi=300)
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    df = get_nuclear_timeseries()

    out_dir = Path("analysis/plots")
    out_dir.mkdir(parents=True, exist_ok=True)
    plot_nuclear_timeseries(df, out_dir / "nuclear_generation_timeseries.png")
