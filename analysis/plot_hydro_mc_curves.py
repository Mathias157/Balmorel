"""Plots of the hydro marginal cost curves of analysis/hydro_mc_curves.py.

Two figures, from the files that script wrote to analysis/output/hydro_mc/<year>:

1. hydro_mc_curves_<year>: the final curves. One panel per area with MC
   steps: the GOMVCOSTO VOM of each step against the step's slice of the
   area's reservoir capacity (steps.csv), with the median curve of the
   passing zones in grey for reference. Areas that fall back to the median
   are marked.

2. hydro_mc_hours_<region>_<year> (with --region): the hours behind a
   region's curve. The ENTSO-E hours of the region's zone are recomputed
   with hydro_mc_curves' own functions:
   - top: every hour of the year (week x hour of week), coloured by the
     utilisation band that the comonotone pairing gives it. Grey hours are
     in the data but not used: their band has fewer than --min-hours hours
     (left out of the regression), or their week has a single band (no
     within-week contrast, so the week effect absorbs them). Blank hours
     have no hydro or no price.
   - bottom left: one week (--week, default the week whose rank correlation
     is closest to the zone's median). Each hour keeps its price and is
     moved to the hydro output of the same rank in the week.
   - bottom right: all used hours, price minus the hour's week effect (the
     week's lowest-band price level), in EUR2016 on the VOM scale. The
     regression's band premia are their band means; the staircase is the
     GOMVCOSTO steps written for the region's area.
   The hours are also written to hours_<zone>.csv next to the curves.

Where the region's zone fails the quality gate, Balmorel uses the median
curve and the zone's hours are not used; the figure says so and draws the
zone's own (rejected) curve dashed. Regions whose zone has no data (e.g.
TR) have no hours to show.

The recomputed curve is checked against curves.csv. A mismatch means the
curves were written with other --bands/--min-hours or other data.

Run from the repo root, after analysis/hydro_mc_curves.py:
    pixi run python analysis/plot_hydro_mc_curves.py 2023
    pixi run python analysis/plot_hydro_mc_curves.py 2023 --region NO2 --region FIN
    pixi run python analysis/plot_hydro_mc_curves.py 2023 -r NO2 --week 2023-01-16
"""

from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hydro_mc_curves import (
    TIME_ZONE,
    band_premia,
    comonotone,
    hydro_and_price,
    isotonic,
    smooth,
    step_voms,
    week_of,
)
from matplotlib import font_manager
from matplotlib.collections import LineCollection
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from pybalmorel.backcasting.__main__ import PRICE_DURATION_REGION_ORDER
from pybalmorel.backcasting.plotstyle import BALMOREL_COLOUR, plot_style
from pybalmorel.backcasting.pricelevel import PRICE_YEAR, deflator

FONT_DIR = Path.home() / ".local/share/fonts/Inter/extras/ttf"  # not on matplotlib's search path
# Sequential blue ramp (dataviz reference palette), low band to high band. On
# a dark surface a high band is light, on a light surface it is dark.
RAMP = {
    "dark": ["#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"],
    "light": ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"],
}
HOURS_PER_WEEK = 168
QUANTILE = 0.999  # K, as in hydro_mc_curves.supply_curve


def set_font():
    for ttf in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(
        (f for f in ("Inter", "Noto Sans") if f in available), "DejaVu Sans"
    )


def band_colours(style: str, bands: int) -> list:
    return list(LinearSegmentedColormap.from_list("bands", RAMP[style])(np.linspace(0, 1, bands)))


def tidy(ax, tokens, grid_axis="y"):
    for side in ax.spines.values():
        side.set_visible(False)
    if grid_axis:
        ax.grid(axis=grid_axis, color=tokens["grid"], lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", length=0, labelsize=6, colors=tokens["muted"])


def save(fig, path: Path):
    for ext in ("pdf", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), transparent=True, dpi=300, bbox_inches="tight")
    print("saved", path.with_suffix(".pdf"), "+ .png")


# ------------------------------- #
#        1. Final curves          #
# ------------------------------- #


def read_outputs(mc_path: Path):
    """curves.csv, diagnostics.csv and steps.csv of a hydro_mc_curves run,
    and the VOM of step 1 (the run's --lowest-vom)."""
    if not (mc_path / "steps.csv").exists():
        raise click.UsageError(f"No steps.csv in {mc_path}: run analysis/hydro_mc_curves.py first")
    curves = pd.read_csv(mc_path / "curves.csv", index_col="Zone")
    curves.columns = curves.columns.astype(int)
    diagnostics = pd.read_csv(mc_path / "diagnostics.csv", index_col="Zone")
    steps = pd.read_csv(mc_path / "steps.csv")
    lowest_vom = steps.loc[steps.Step == 1, "VOM"].iloc[0]
    return curves, diagnostics, steps, lowest_vom


def stairs(area_steps: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Edges (share of the area's step capacity) and VOM of an area's steps."""
    per_step = area_steps.groupby("Step").agg(Capacity=("Capacity", "sum"), VOM=("VOM", "first"))
    total = per_step.Capacity.sum()
    edges = (np.r_[0, per_step.Capacity.cumsum().values] / total if total > 0
             else np.linspace(0, 1, len(per_step) + 1))
    return edges, per_step.VOM.values


def area_order(steps: pd.DataFrame) -> list[str]:
    """Areas in the house region order (PRICE_DURATION_REGION_ORDER), by
    region, else zone, else the zone's country; unknown ones last."""
    order = {r: i for i, r in enumerate(PRICE_DURATION_REGION_ORDER)}
    first = steps.groupby("Area")[["Region", "Zone"]].first()

    def key(area):
        region, zone = first.loc[area]
        for name in (region, zone, zone.split("-")[0]):
            if name in order:
                return (order[name], area)
        return (len(order), area)

    return sorted(first.index, key=key)


def gate_reason(zone: str, diagnostics: pd.DataFrame) -> str:
    reason = (diagnostics.reason.get(zone) if zone in diagnostics.index
              else "not an ENTSO-E zone of the run")
    return reason if isinstance(reason, str) and reason else "fails the gate"


def draw_curves(curves, diagnostics, steps, lowest_vom, year, style):
    areas = area_order(steps)
    regions = steps.groupby("Area").Region.first()
    shared = regions.value_counts()
    cols = 8
    rows = int(np.ceil(len(areas) / cols))
    with plot_style(style) as (tokens, _):
        fig, axes = plt.subplots(rows, cols, figsize=(6.4, 1.0 + 0.95 * rows),
                                 sharex=True, sharey=True)
        fig.subplots_adjust(left=0.07, right=0.985, top=1 - 0.62 / (1.0 + 0.95 * rows),
                            bottom=0.62 / (1.0 + 0.95 * rows), wspace=0.12, hspace=0.42)
        axes = axes.ravel()
        top = steps.VOM.max()
        for ax, area in zip(axes, areas):
            area_steps = steps[steps.Area == area]
            region, zone, source = area_steps[["Region", "Zone", "Curve"]].iloc[0]
            edges, vom = stairs(area_steps)
            capacity = area_steps.groupby("Step").Capacity.sum()
            median = step_voms(curves.loc["median"], capacity, lowest_vom).values
            ax.stairs(median, edges, color=tokens["axis"], lw=0.9, baseline=None, zorder=2)
            ax.stairs(vom, edges, color=BALMOREL_COLOUR, lw=1.4, baseline=None, zorder=3)
            label = region if shared[region] == 1 else f"{region} {area}"
            ax.set_title(label, loc="left", fontsize=6.5, fontweight="semibold",
                         color=tokens["ink"], pad=2)
            total = capacity.sum()
            note = f"{total / 1e3:.1f} GW" if total >= 1e3 else f"{total:.0f} MW"
            if source == "median":
                note = f"median · {note}"
            elif zone != region:
                note = f"{zone} · {note}"
            # Top left is free: every curve starts low and the top gridline is lower
            ax.text(0.02, 0.98, note, transform=ax.transAxes, fontsize=5, color=tokens["muted"],
                    va="top")
            tidy(ax, tokens)
        for ax in axes[len(areas):]:
            ax.set_visible(False)
        axes[0].set_xlim(0, 1)
        axes[0].set_ylim(0, top * 1.05)
        axes[0].set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        axes[0].yaxis.set_major_locator(plt.MaxNLocator(3))
        for ax in axes:  # keep the 1 and the next panel's 0 apart
            ticks = ax.xaxis.get_major_ticks()
            ticks[0].label1.set_horizontalalignment("left")
            ticks[-1].label1.set_horizontalalignment("right")

        height = fig.get_figheight()
        fig.text(0.07, 1 - 0.12 / height, f"Reservoir hydro marginal cost steps  ·  "
                 f"€{PRICE_YEAR}/MWh", fontsize=9, fontweight="semibold", color=tokens["ink"],
                 va="top")
        fig.text(0.07, 1 - 0.32 / height,
                 f"GOMVCOSTO of GNR_RES_WTR_NOPMP_MC-01..10 from ENTSO-E {year}  ·  "
                 "x: share of the area's reservoir hydro capacity",
                 fontsize=6.5, color=tokens["muted"], va="top")
        handles = [Line2D([], [], color=BALMOREL_COLOUR, lw=1.4, label="Area's steps"),
                   Line2D([], [], color=tokens["axis"], lw=0.9, label="Median of passing zones")]
        fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 1 - 0.08 / height),
                   ncol=2, frameon=False, fontsize=6.5, handlelength=1.6, columnspacing=1.2)
        fallback = sorted({f"{r} ({gate_reason(z, diagnostics)})" for r, z, c in
                           steps.groupby("Area")[["Region", "Zone", "Curve"]].first().values
                           if c == "median"})
        fig.text(0.07, 0.02 / height,
                 "Step 1 is anchored at the --lowest-vom; each step's VOM is the curve's mean "
                 "over its capacity slice. Under each title: the zone whose curve the area "
                 "gets, where it isn't the region, and the area's reservoir capacity.\n"
                 "Median: " + "; ".join(fallback),
                 fontsize=4.5, color=tokens["muted"], va="bottom", wrap=True)
    return fig


# ------------------------------- #
#     2. The hours of a region    #
# ------------------------------- #


def find_areas(name: str, steps: pd.DataFrame) -> pd.DataFrame:
    """The MC steps of the areas a region, zone or area name picks."""
    for column in ("Region", "Zone", "Area"):
        if (picked := steps[steps[column] == name]).size:
            return picked
    known = ", ".join(sorted(steps.Region.unique()))
    raise click.BadParameter(f"{name!r} is no region, zone or area with MC steps ({known})",
                             param_hint="--region")


def zone_hours(entsoe_path: Path, year: int, zone: str, bands: int, min_hours: int):
    """The hourly data of `zone` as hydro_mc_curves uses it: one row per hour
    with its week, utilisation, comonotone band, whether the regression uses
    it, and its price minus the week effect (nominal, relative to the
    curve's lowest band). Also the band premia, hours per band and the
    smoothed curve (nominal), and a note on hours dropped for missing data."""
    df, kind = hydro_and_price(entsoe_path, year, zone)
    if df is None:
        return None, kind
    week = week_of(df.index)
    capacity = df.h.quantile(QUANTILE)
    paired = comonotone(df.h, df.p, week)
    band = pd.Series(np.clip((paired / capacity * bands).astype(int), 0, bands - 1), index=df.index)
    premia, hours = band_premia(df.p, band, week, bands, min_hours)
    estimated = premia.dropna()

    hourly = pd.DataFrame({
        "hydro_MW": df.h, "price": df.p, "week": week,
        "u": df.h / capacity, "u_paired": paired / capacity, "band": band,
    })
    in_estimated = band.isin(estimated.index)
    contrast = in_estimated.groupby(week).transform(
        lambda used: band[used.index][used].nunique() > 1)
    hourly["used"] = in_estimated & contrast
    hourly["reason"] = np.where(~in_estimated, f"band < {min_hours} h",
                                np.where(~contrast, "single band in week", ""))

    # Week effect: the week's lowest-band price level, a_w = mean(p) - mean(beta_band)
    beta = band.map(premia).where(hourly.used)
    effect = (hourly.price.where(hourly.used).groupby(week).transform("mean")
              - beta.groupby(week).transform("mean"))
    offset = isotonic(estimated.values, hours[estimated.index].values)[0] if len(estimated) else 0
    hourly["over_week_effect"] = hourly.price - effect - offset

    curve = smooth(premia, hours)
    rank_corr = df.groupby(week).apply(lambda w: w.h.corr(w.p, method="spearman"))
    return dict(hourly=hourly, premia=premia - offset, hours=hours, curve=curve, kind=kind,
                capacity=capacity, rank_corr=rank_corr), None


def pick_week(rank_corr: pd.Series, week: str | None) -> pd.Timestamp:
    """The Monday of the week holding date `week`, else the week whose rank
    correlation is closest to the median."""
    if week:
        monday = pd.Timestamp(week).to_period("W-SUN").start_time
        if monday not in rank_corr.index:
            raise click.BadParameter(f"No data in the week of {week}", param_hint="--week")
        return monday
    return (rank_corr - rank_corr.median()).abs().idxmin()


def heatmap(ax, hourly, bands, colours, tokens, year):
    """Week x hour-of-week map of the bands; grey = not used, blank = no data."""
    local = hourly.index.tz_convert(TIME_ZONE)
    weeks = np.sort(hourly.week.unique())
    row = pd.Index(weeks).get_indexer(hourly.week)
    column = local.dayofweek * 24 + local.hour
    grid = np.full((len(weeks), HOURS_PER_WEEK), np.nan)
    grid[row, column] = np.where(hourly.used, hourly.band, -1)

    cmap = ListedColormap([tokens["grid"]] + colours)
    cmap.set_bad((0, 0, 0, 0))
    ax.imshow(np.ma.masked_invalid(grid), cmap=cmap, norm=BoundaryNorm(np.arange(-1.5, bands), cmap.N),
              aspect="auto", interpolation="nearest")
    for day in range(1, 7):
        ax.axvline(day * 24 - 0.5, color=tokens["surface"], lw=0.8)
    ax.set_xticks(np.arange(7) * 24 + 11.5, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    mondays = [pd.Timestamp(w) for w in weeks]
    ticks = [(i, w) for i, w in enumerate(mondays)
             if w.year == year and (i == 0 or w.month != mondays[i - 1].month)]
    ax.set_yticks([i for i, _ in ticks], [w.strftime("%b") for _, w in ticks])
    tidy(ax, tokens, grid_axis=None)
    return weeks


def week_panel(ax, hourly, monday, bands, colours, tokens):
    """One week: each hour moves from its own output to the output of the
    same rank in the week (comonotone pairing), at its own price."""
    w = hourly[hourly.week == monday]
    segments = np.stack([np.c_[w.u, w.price], np.c_[w.u_paired, w.price]], axis=1)
    ax.add_collection(LineCollection(segments, colors=tokens["grid"], lw=0.5, zorder=2))
    ax.scatter(w.u, w.price, s=6, facecolor="none", edgecolor=tokens["axis"], lw=0.5, zorder=3)
    ax.scatter(w.u_paired, w.price, s=7, color=[colours[b] for b in w.band],
               edgecolor="none", zorder=4)
    for edge in np.arange(1, bands) / bands:
        ax.axvline(edge, color=tokens["grid"], lw=0.4, ls=(0, (1, 2)), zorder=1)
    ax.set_xlim(0, 1.02)
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    ax.set_xlabel("hydro output / K", fontsize=6, color=tokens["ink2"], labelpad=2)
    ax.set_ylabel("€/MWh (nominal)", fontsize=6, color=tokens["ink2"], labelpad=2)
    rho = w.u.corr(w.price, method="spearman")
    ax.legend(handles=[
        Line2D([], [], ls="", marker="o", ms=3, mfc="none", mec=tokens["axis"], mew=0.5,
               label="hour as reported"),
        Line2D([], [], ls="", marker="o", ms=3, mfc=colours[bands // 2], mec="none",
               label="its price, same-rank output"),
    ], loc="upper left", frameon=False, fontsize=5, handletextpad=0.2, borderaxespad=0.1)
    ax.set_title(f"Week of {monday:%d %b} (outlined), ρ = {rho:.2f}", loc="left",
                 fontsize=7, fontweight="semibold", color=tokens["ink"], pad=4)
    tidy(ax, tokens, grid_axis="y")


def residual_panel(ax, data, area_steps, own, to_2016, lowest_vom, bands, colours, tokens):
    """All used hours over their week effect against the final steps."""
    hourly = data["hourly"]
    used = hourly[hourly.used]
    y = used.over_week_effect * to_2016 + lowest_vom
    ax.scatter(used.u_paired, y, s=1.2, color=[colours[b] for b in used.band], alpha=0.35,
               edgecolor="none", rasterized=True, zorder=2)
    centres = (np.arange(bands) + 0.5) / bands
    premia = data["premia"] * to_2016 + lowest_vom
    ax.scatter(centres, premia, s=16, facecolor=tokens["surface"], edgecolor=tokens["ink"],
               lw=0.8, zorder=5)
    if not own:
        ax.stairs(data["curve"].values * to_2016 + lowest_vom, np.arange(bands + 1) / bands,
                  color=tokens["ink"], lw=1.1, ls=(0, (3, 2)), baseline=None, zorder=4)
    edges, vom = stairs(area_steps)
    ax.stairs(vom, edges, color=BALMOREL_COLOUR, lw=1.6, baseline=None, zorder=4)
    lo, hi = np.nanpercentile(y, [1, 99])
    lo, hi = min(lo, np.nanmin(premia), 0), max(hi, np.nanmax(premia), vom.max())
    ax.set_ylim(lo - 0.04 * (hi - lo), hi + 0.04 * (hi - lo))
    ax.set_xlim(0, 1.02)
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    ax.set_xlabel("paired hydro output / K  =  share of step capacity", fontsize=6,
                  color=tokens["ink2"], labelpad=2)
    ax.set_ylabel(f"€{PRICE_YEAR}/MWh (VOM scale)", fontsize=6, color=tokens["ink2"], labelpad=2)
    ax.set_title(f"{len(used):,} used hours: price − week effect", loc="left", fontsize=7,
                 fontweight="semibold", color=tokens["ink"], pad=4)
    tidy(ax, tokens, grid_axis="y")
    handles = [
        Line2D([], [], ls="", marker="o", ms=4, mfc=tokens["surface"], mec=tokens["ink"],
               mew=0.8, label="Band premium (regression)"),
        Line2D([], [], color=BALMOREL_COLOUR, lw=1.6, label="GOMVCOSTO steps"),
    ]
    if not own:
        handles.append(Line2D([], [], color=tokens["ink"], lw=1.1, ls=(0, (3, 2)),
                              label="Zone's own curve (rejected)"))
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=5.5, handlelength=1.6,
              borderaxespad=0.2)


def draw_hours(data, area_steps, diagnostics, lowest_vom, year, monday, min_hours, style):
    region, zone, source = area_steps[["Region", "Zone", "Curve"]].iloc[0]
    own = source != "median"
    hourly, bands = data["hourly"], len(data["curve"])
    to_2016 = deflator(year)
    with plot_style(style) as (tokens, _):
        colours = band_colours(style, bands)
        fig = plt.figure(figsize=(6.4, 5.4))
        grid = fig.add_gridspec(2, 2, height_ratios=[1.25, 1], width_ratios=[1, 1.35],
                                left=0.08, right=0.9, top=0.86, bottom=0.12,
                                hspace=0.38, wspace=0.22)
        ax_map = fig.add_subplot(grid[0, :])
        heatmap(ax_map, hourly, bands, colours, tokens, year)
        ax_map.set_title("Every hour, by its utilisation band after pairing", loc="left",
                         fontsize=7, fontweight="semibold", color=tokens["ink"], pad=4)

        # Band key, beside the map
        key = fig.add_axes([0.915, ax_map.get_position().y0, 0.018, ax_map.get_position().height])
        key.imshow(np.arange(bands)[::-1, None], cmap=ListedColormap(colours), aspect="auto")
        key.set_xticks([])
        key.set_yticks(range(bands), [f"{b / bands:.1f}–{(b + 1) / bands:.1f}"
                                      for b in range(bands)][::-1])
        key.yaxis.tick_right()
        key.tick_params(length=0, labelsize=5, colors=tokens["muted"], pad=2)
        for side in key.spines.values():
            side.set_visible(False)
        key.set_title("u", fontsize=6, color=tokens["ink2"], pad=3)
        fig.legend(handles=[Patch(color=tokens["grid"], label="not used")],
                   loc="upper left", bbox_to_anchor=(0.905, ax_map.get_position().y0 - 0.005),
                   frameon=False, fontsize=5, handlelength=0.9, handleheight=0.9,
                   handletextpad=0.4, borderaxespad=0)

        ax_week = fig.add_subplot(grid[1, 0])
        week_panel(ax_week, hourly, monday, bands, colours, tokens)
        row = list(np.sort(hourly.week.unique())).index(monday)
        ax_map.add_patch(Rectangle((-0.5, row - 0.5), HOURS_PER_WEEK, 1, facecolor="none",
                                   edgecolor=tokens["ink"], lw=0.7, zorder=5))

        ax_res = fig.add_subplot(grid[1, 1])
        residual_panel(ax_res, data, area_steps, own, to_2016, lowest_vom, bands, colours, tokens)

        diag = diagnostics.loc[zone]
        verdict = ("passes the gate" if own else
                   f"fails the gate ({gate_reason(zone, diagnostics)}): Balmorel uses the "
                   "median curve, these hours are not used")
        areas = ", ".join(area_steps.Area.unique())
        fig.text(0.08, 0.975, f"Hours behind the hydro marginal cost steps of {region}  ·  "
                 f"ENTSO-E {year}", fontsize=9, fontweight="semibold", color=tokens["ink"],
                 va="top")
        fig.text(0.08, 0.945,
                 f"Zone {zone} ({data['kind']} hydro, K = {data['capacity']:,.0f} MW, median "
                 f"within-week ρ = {diag.rank_corr:.2f}) {verdict}. Area {areas}.",
                 fontsize=6, color=tokens["muted"], va="top")
        dropped = data["hourly"].reason.value_counts().drop("", errors="ignore")
        unused = "; ".join(f"{n:,} h {r}" for r, n in dropped.items()) or "none"
        fig.text(0.08, 0.015,
                 f"K = 99.9th percentile of hourly output. Within each Monday–Sunday week the "
                 f"outputs are paired with the prices by rank; price is then regressed on week "
                 f"effects plus {bands} bands of paired u.\n"
                 f"Not used: {unused}. Blank: no hydro or no price. Right: price minus the week "
                 f"effect (the week's lowest-band level), × deflator, + step-1 VOM; y clipped to "
                 f"the 1–99th percentile.",
                 fontsize=4.5, color=tokens["muted"], va="bottom")
    return fig


def check_curve(data, curves, zone, to_2016, bands, min_hours):
    """Warn if the recomputed curve isn't the one in curves.csv."""
    if zone not in curves.index:
        return
    gap = np.abs(data["curve"].values * to_2016 - curves.loc[zone].values).max()
    if gap > 0.01:
        print(f"WARNING: {zone}'s recomputed curve differs from curves.csv by up to "
              f"{gap:.2f} €{PRICE_YEAR}/MWh. Was it written with --bands {bands} "
              f"--min-hours {min_hours} and the same ENTSO-E files?")


@click.command()
@click.argument("year", type=int)
@click.option("--region", "-r", "regions", multiple=True,
              help="Also plot the hours behind this region's curve (Balmorel region, ENTSO-E "
              "zone or area, e.g. NO2, FIN, IT-NORD). Repeatable")
@click.option("--week", default=None,
              help="A date in the example week, e.g. 2023-01-16 [default: the week whose rank "
              "correlation is closest to the zone's median]")
@click.option("--min-hours", default=50, show_default=True,
              help="As given to hydro_mc_curves.py")
@click.option("--entsoe-path", default="backcast/entsoedata", show_default=True)
@click.option("--mc-path", default="analysis/output/hydro_mc", show_default=True,
              help="Output folder of hydro_mc_curves.py (without the year)")
@click.option("--plot-path", default="analysis/plots", show_default=True)
@click.option("--style", type=click.Choice(["dark", "light"]), default="dark", show_default=True)
@click.option("--no-overview", is_flag=True, help="Skip the figure of all areas' curves")
def main(year, regions, week, min_hours, entsoe_path, mc_path, plot_path, style, no_overview):
    mc_path, plot_path = Path(mc_path) / str(year), Path(plot_path)
    curves, diagnostics, steps, lowest_vom = read_outputs(mc_path)
    plot_path.mkdir(parents=True, exist_ok=True)
    set_font()

    if not no_overview:
        fig = draw_curves(curves, diagnostics, steps, lowest_vom, year, style)
        save(fig, plot_path / f"hydro_mc_curves_{year}")
        plt.close(fig)

    bands = len(curves.columns)
    for name in regions:
        picked = find_areas(name, steps)
        for (region, zone), area_steps in picked.groupby(["Region", "Zone"]):
            data, reason = zone_hours(Path(entsoe_path), year, zone, bands, min_hours)
            if data is None:
                print(f"{region}: zone {zone} has {reason}; its areas use the median of the "
                      "passing zones' curves, so there are no hours of its own to show")
                continue
            check_curve(data, curves, zone, deflator(year), bands, min_hours)
            data["hourly"].round(dict.fromkeys(["u", "u_paired", "over_week_effect"], 4)).to_csv(mc_path / f"hours_{zone}.csv",
                                           index_label="Time_UTC")
            print("saved", mc_path / f"hours_{zone}.csv")
            monday = pick_week(data["rank_corr"], week)
            fig = draw_hours(data, area_steps, diagnostics, lowest_vom, year, monday,
                             min_hours, style)
            save(fig, plot_path / f"hydro_mc_hours_{region}_{year}")
            plt.close(fig)


if __name__ == "__main__":
    main()
