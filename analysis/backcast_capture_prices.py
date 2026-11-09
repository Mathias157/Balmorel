"""Capture prices of wind and solar in a backcast, against ENTSO-E.

The capture price of a technology in a region is the price its output
earned on average: sum(output x price) / sum(output), summed over the hours
and over the region's zones, each zone at its own price (Balmorel's DE4-*,
ENTSO-E's IT-*). The capture rate (value factor) is the capture price over
the region's baseload price, the mean of its zones' hourly prices.

Both sides are compared on the same hours: the solved hours of the Balmorel
run in which ENTSO-E reports a price and some generation in every zone of the
region. ENTSO-E's missing wind or solar in those hours counts as 0.

Technologies: ENTSO-E Wind Onshore, Wind Offshore and Solar against Balmorel
WIND-ON, WIND-OFF and SOLAR-PV. Balmorel splits existing capacity into
resource grades (RG1-RG3). They are written to their own CSV, not plotted:
in backcast_R2023 most regions give all their grades one profile, so the
grades' capture prices differ by under 0.5 €/MWh (BG solar 1.7).

Balmorel prices are in EUR2016 and converted to nominal EUR of the backcast
year, as ENTSO-E's are. Capture rates don't depend on the price level.

Run from the repo root (GAMS_SYSTEM_DIR comes from .env):
    pixi run python analysis/backcast_capture_prices.py
"""

from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D
from pybalmorel.backcasting.__main__ import (
    PRICE_DURATION_REGION_ORDER,
    balmorel_prices_in_year,
    format_entsoe_data,
    load_balmorel_data,
    load_observed_prices,
)
from pybalmorel.backcasting.calendar import backcast_hours, from_backcast_grid
from pybalmorel.backcasting.flows import canonical_region
from pybalmorel.backcasting.plotstyle import BALMOREL_COLOUR, ENTSOE_COLOUR, plot_style

TECHNOLOGIES = ["Onshore wind", "Offshore wind", "Solar PV"]
BALMOREL_TECHNOLOGIES = {
    "WIND-ON": "Onshore wind",
    "WIND-OFF": "Offshore wind",
    "SOLAR-PV": "Solar PV",
}
ENTSOE_TECHNOLOGIES = {
    "Wind Onshore": "Onshore wind",
    "Wind Offshore": "Offshore wind",
    "Solar": "Solar PV",
}
ALL_GRADES = "All"
EUROPE = "Europe"
SOURCES = {"ENTSOE": "ENTSO-E", "BALMOREL": "Balmorel"}
METRICS = {
    "capture_price": ("Capture price", "€{year}/MWh (nominal)"),
    "capture_rate": ("Capture rate", "capture price / baseload price"),
}

FONT_DIR = Path.home() / ".local/share/fonts/Inter/extras/ttf"  # not on matplotlib's search path


def set_font():
    for ttf in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(
        (f for f in ("Inter", "Noto Sans") if f in available), "DejaVu Sans"
    )


# ------------------------------- #
#             Data                #
# ------------------------------- #


def balmorel_data(scenario: str, scenario_path: str, year: int, overwrite: bool):
    """Hourly Balmorel wind and solar output per zone and resource grade, and
    hourly prices per zone (nominal EUR of `year`, solved hours only).

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Output with columns 'Zone',
            'Technology', 'Grade', 'Time', 'Value' (MW), and prices with index
            'Time' and one column per zone.
    """
    _, prices, generation, _ = load_balmorel_data(scenario, scenario_path, year, overwrite)
    cached = set(generation.Scenario.unique()) | set(prices.Scenario.unique())
    if cached != {scenario}:
        raise click.UsageError(
            f"{scenario_path}/backcastoutput holds {sorted(cached)}, not {scenario}. "
            "Rerun with --overwrite to read the scenario's MainResults."
        )

    vre = generation[generation.Technology.isin(BALMOREL_TECHNOLOGIES)]
    vre = vre.assign(
        Technology=vre.Technology.map(BALMOREL_TECHNOLOGIES),
        Grade=vre.Generation.str.extract(r"_(RG\d+)", expand=False).fillna("n/a"),
    )
    vre = from_backcast_grid(
        vre.groupby(["Region", "Technology", "Grade", "Season", "Time"], as_index=False)
        .Value.sum(),
        year,
    ).rename(columns={"Region": "Zone"})

    prices = from_backcast_grid(prices[["Region", "Season", "Time", "Value"]], year)
    prices = balmorel_prices_in_year(prices, year).pivot_table(
        index="Time", columns="Region", values="Value"
    )
    # MainResults leaves out zeros: a zone without a price in a solved hour had 0
    return vre, prices.fillna(0)


def entsoe_data(entsoe_path: str, year: int):
    """Hourly ENTSO-E wind and solar output and prices per zone.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: Output with columns
            'Zone', 'Technology', 'Time', 'Value' (MW, NaN where not
            reported); prices with index 'Time' and one column per zone; and
            a boolean frame of the same shape, True where the zone reports
            some generation in that hour.
    """
    output, reported = [], {}
    for file in sorted(Path(entsoe_path).glob(f"{year}_*_generation.csv")):
        df = format_entsoe_data(pd.read_csv(file, low_memory=False), "h", file, year, "generation")
        zone = df.Region.iloc[0]
        df = df.drop(columns="Region").set_index("Time")
        reported[zone] = df.notna().any(axis=1)
        vre = df.reindex(columns=list(ENTSOE_TECHNOLOGIES)).rename(columns=ENTSOE_TECHNOLOGIES)
        vre.columns.name = "Technology"
        output.append(vre.stack(future_stack=True).rename("Value").reset_index().assign(Zone=zone))

    return (
        pd.concat(output, ignore_index=True),
        load_observed_prices(entsoe_path, year),
        pd.DataFrame(reported).fillna(False),
    )


def region_hours(e_prices: pd.DataFrame, e_reported: pd.DataFrame, solved: pd.Index) -> dict:
    """Per canonical region, the solved hours in which every ENTSO-E zone of
    the region reports a price and some generation."""
    valid = e_prices.notna() & e_reported.reindex_like(e_prices).fillna(False).astype(bool)
    valid = valid.reindex(solved, fill_value=False)
    by_region = valid.T.groupby(canonical_region).all().T
    return {r: by_region.index[by_region[r]] for r in by_region.columns if by_region[r].any()}


def revenue(output: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """`output` with its zone's price, 'Revenue' = output x price, and the
    canonical 'Region'."""
    price = prices.stack().rename("Price").rename_axis(["Time", "Zone"]).reset_index()
    df = output.merge(price, on=["Zone", "Time"], how="inner")
    return df.assign(Revenue=df.Value * df.Price, Region=df.Zone.map(canonical_region))


def baseload(prices: pd.DataFrame, hours: dict) -> pd.Series:
    """Mean over hours of the region's mean zone price, per canonical region."""
    hourly = prices.T.groupby(canonical_region).mean().T
    return pd.Series({r: hourly.loc[h, r].mean() for r, h in hours.items() if r in hourly})


def capture(df: pd.DataFrame, hours: dict, keys: list[str], n_year: int) -> pd.DataFrame:
    """Capture price and annual TWh per `keys`, over each region's hours."""
    mask = pd.Series(False, index=df.index)
    for region, h in hours.items():
        mask |= (df.Region == region) & df.Time.isin(h)
    sums = df[mask].groupby(keys)[["Value", "Revenue"]].sum()
    n_hours = sums.index.get_level_values("Region").map(lambda r: len(hours[r]))
    return pd.DataFrame({
        "capture_price": sums.Revenue / sums.Value,
        "TWh": sums.Value / n_hours * n_year / 1e6,
        "Revenue": sums.Revenue / n_hours * n_year,
    })


def capture_table(b_out, b_prices, e_out, e_prices, e_reported, year: int):
    """Capture prices and rates on both sides per region and technology, plus
    Balmorel's per resource grade.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Region x Technology rows with
            columns (metric, source); and Balmorel's per Region, Technology,
            Grade.
    """
    hours = region_hours(e_prices, e_reported, b_prices.index)
    n_year = len(backcast_hours(year))

    e = revenue(e_out.fillna({"Value": 0}), e_prices)
    b = revenue(b_out, b_prices)

    table = pd.concat(
        {
            "ENTSOE": capture(e, hours, ["Region", "Technology"], n_year),
            "BALMOREL": capture(b, hours, ["Region", "Technology"], n_year),
        },
        axis=1,
    ).swaplevel(axis=1)
    grades = capture(b, hours, ["Region", "Technology", "Grade"], n_year)

    base = {"ENTSOE": baseload(e_prices, hours), "BALMOREL": baseload(b_prices, hours)}
    regions = table.index.get_level_values("Region")
    for source in SOURCES:
        table[("baseload", source)] = regions.map(base[source])
        table[("capture_rate", source)] = (
            table[("capture_price", source)] / table[("baseload", source)]
        )
    grades["capture_rate"] = grades.capture_price / grades.index.get_level_values(
        "Region"
    ).map(base["BALMOREL"])
    table[("hours", "")] = regions.map(lambda r: len(hours.get(r, [])))

    return table.sort_index(axis=1), grades


def europe(table: pd.DataFrame, compared: pd.Index) -> pd.DataFrame:
    """Output-weighted capture price and rate over the compared regions, per
    technology. The rate is the capture price over the output-weighted
    baseload price."""
    rows = {}
    for tech in TECHNOLOGIES:
        t = table.loc[[i for i in compared if i[1] == tech]]
        if t.empty:
            continue
        row = {}
        for s in SOURCES:
            twh = t[("TWh", s)]
            row[("TWh", s)] = twh.sum()
            row[("capture_price", s)] = t[("Revenue", s)].sum() / twh.sum() / 1e6
            row[("baseload", s)] = (t[("baseload", s)] * twh).sum() / twh.sum()
            row[("capture_rate", s)] = row[("capture_price", s)] / row[("baseload", s)]
        rows[(EUROPE, tech)] = row
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.names = ["Region", "Technology"]
    out.columns = pd.MultiIndex.from_tuples(out.columns)
    return out


# ------------------------------- #
#            Drawing              #
# ------------------------------- #


def region_order(regions) -> list[str]:
    known = [r for r in PRICE_DURATION_REGION_ORDER if r in regions]
    return known + sorted(set(regions) - set(known))


def draw(table, compared, metric: str, year: int, scenario: str, style: str):
    """Dot plot per technology: ENTSO-E and Balmorel per region, joined by a
    line; Europe on top."""
    title, unit = METRICS[metric]
    unit = unit.format(year=year)
    regions = region_order({r for r, _ in compared})
    y = {r: i for i, r in enumerate(regions)} | {EUROPE: -1.3}  # Europe set apart on top

    with plot_style(style) as (tokens, _):
        fig, axes = plt.subplots(1, len(TECHNOLOGIES), figsize=(6.4, 4.4), sharey=True)
        fig.subplots_adjust(left=0.07, right=0.985, top=0.83, bottom=0.12, wspace=0.08)
        values = []
        for ax, tech in zip(axes, TECHNOLOGIES):
            keys = [i for i in compared if i[1] == tech] + [
                i for i in table.index if i == (EUROPE, tech)
            ]
            for region, _ in keys:
                yi = y[region]
                e = table.loc[(region, tech), (metric, "ENTSOE")]
                b = table.loc[(region, tech), (metric, "BALMOREL")]
                ax.plot([e, b], [yi, yi], color=tokens["axis"], lw=0.8, zorder=2,
                        solid_capstyle="round")
                size = 26 if region == EUROPE else 16
                for v, colour in ((e, ENTSOE_COLOUR), (b, BALMOREL_COLOUR)):
                    ax.scatter(v, yi, s=size, color=colour, edgecolor=tokens["surface"],
                               lw=0.6, zorder=4)
                values += [e, b]

            ax.set_title(tech, loc="left", fontsize=8, fontweight="semibold", pad=4,
                         color=tokens["ink"])
            ax.axhline(-0.65, color=tokens["grid"], lw=0.5, zorder=1)
            ax.grid(axis="x", color=tokens["grid"], lw=0.5, zorder=0)
            ax.set_axisbelow(True)
            for side in ax.spines.values():
                side.set_visible(False)
            ax.tick_params(axis="both", length=0, labelsize=6.5, colors=tokens["muted"])
            ax.xaxis.set_major_locator(plt.MaxNLocator(4))
            if metric == "capture_rate":
                ax.axvline(1, color=tokens["axis"], lw=0.8, ls=(0, (2, 2)), zorder=1)
                ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")

        lo, hi = np.nanmin(values), np.nanmax(values)
        pad = 0.05 * (hi - lo)
        for ax in axes:
            ax.set_xlim(lo - pad, hi + pad)
        axes[0].set_ylim(len(regions) - 0.4, -1.9)
        axes[0].set_yticks([y[r] for r in [EUROPE] + regions], [EUROPE] + regions, fontsize=6)
        axes[0].get_yticklabels()[0].set_fontweight("semibold")
        for label in axes[0].get_yticklabels():
            label.set_color(tokens["ink2"])

        fig.text(0.07, 0.965, f"{title}  ·  {unit}", fontsize=9, fontweight="semibold",
                 color=tokens["ink"], va="top")
        fig.text(0.07, 0.925, f"Balmorel {scenario.split('_')[-1]} vs ENTSO-E, per region",
                 fontsize=6.5, color=tokens["muted"], va="top")
        handles = [
            Line2D([], [], ls="", marker="o", ms=5, color=ENTSOE_COLOUR, label="ENTSO-E"),
            Line2D([], [], ls="", marker="o", ms=5, color=BALMOREL_COLOUR, label="Balmorel"),
        ]
        fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.975), ncol=3,
                   frameon=False, fontsize=6.5, handletextpad=0.3, columnspacing=1.2)
        fig.text(
            0.07, 0.02,
            "Capture price = Σ output × price / Σ output, each zone at its own price. Regions with "
            "≥ the minimum output on both sides. Europe: output-weighted over the regions shown.\n"
            "Balmorel prices converted from €2016. ENTSO-E books the offshore wind of SE4, FI and IE "
            "as onshore.",
            fontsize=5, color=tokens["muted"], va="bottom",
        )
    return fig


def save(fig, path: Path):
    for ext in ("pdf", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), transparent=True, dpi=300, bbox_inches="tight")
    print("saved", path.with_suffix(".pdf"), "+ .png")


@click.command()
@click.option("--scenario", default="backcast_R2023", show_default=True,
              help="MainResults_<scenario>.gdx")
@click.option("--scenario-path", default="backcast", show_default=True)
@click.option("--entsoe-path", default="backcast/entsoedata", show_default=True)
@click.option("--year", default=2023, show_default=True)
@click.option("--min-twh", default=0.5, show_default=True,
              help="Annual output a technology needs on both sides to be plotted in a region")
@click.option("--style", type=click.Choice(["dark", "light"]), default="dark", show_default=True)
@click.option("--overwrite", is_flag=True,
              help="Reread the MainResults GDX, replacing the scenario folder's backcastoutput "
              "cache (which pybalmorel's format command shares)")
@click.option("--plot-path", default="analysis/plots", show_default=True)
@click.option("--output-path", default="analysis/output", show_default=True)
def main(scenario, scenario_path, entsoe_path, year, min_twh, style, overwrite, plot_path,
         output_path):
    plot_path, output_path = Path(plot_path), Path(output_path)
    set_font()

    b_out, b_prices = balmorel_data(scenario, scenario_path, year, overwrite)
    e_out, e_prices, e_reported = entsoe_data(entsoe_path, year)
    table, grades = capture_table(b_out, b_prices, e_out, e_prices, e_reported, year)

    both = (table[("TWh", "ENTSOE")] >= min_twh) & (table[("TWh", "BALMOREL")] >= min_twh)
    compared = table.index[both.fillna(False)]
    table = pd.concat([table, europe(table, compared)])

    output_path.mkdir(parents=True, exist_ok=True)
    flat = table.drop(columns="Revenue", level=0)
    flat.columns = [f"{s}_{m}" if s else m for m, s in flat.columns]
    flat.round(3).to_csv(output_path / f"capture_prices_{scenario}.csv")
    grades.drop(columns="Revenue").round(3).to_csv(
        output_path / f"capture_prices_grades_{scenario}.csv"
    )
    with pd.option_context("display.width", 200, "display.max_rows", 200):
        print(flat.loc[list(compared) + [i for i in flat.index if i[0] == EUROPE]].round(2))
    skipped = table.index.difference(compared).difference(
        [i for i in table.index if i[0] == EUROPE]
    )
    print(f"Not plotted (< {min_twh} TWh on one side or no data):",
          ", ".join(f"{r} {t}" for r, t in skipped))

    plot_path.mkdir(parents=True, exist_ok=True)
    for metric in METRICS:
        fig = draw(table, compared, metric, year, scenario, style)
        save(fig, plot_path / f"backcast_{metric}s_{scenario.split('_')[-1]}")
        plt.close(fig)


if __name__ == "__main__":
    main()
