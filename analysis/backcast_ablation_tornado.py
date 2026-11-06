"""Tornado plots of the leave-one-out backcast ablation (F2023).

Each ablation run `backcast_abl_<name>` is the F2023 backcast with one
development removed; `backcast_abl_ref` has all of them. Per metric, a bar is
error(without the development) - error(ref): positive means the development
improved the fit to ENTSO-E.

Metrics, all over the regions that ENTSO-E and every run have in common:
- Generation: sum over region x category of |Balmorel - ENTSO-E|, annual TWh.
  F only solves every 7th hour, so both sides are compared at F's hours and
  scaled to the 8736-hour year (pybalmorel's join_generation would otherwise
  zero-fill Balmorel's missing hours).
- Load: sum over regions of |Balmorel - ENTSO-E|, annual TWh (same scaling).
- Price MAE: mean hourly |Balmorel - ENTSO-E| over region-hours, EUR2023/MWh.
- Price spread: mean over regions of |std(Balmorel) - std(ENTSO-E)|, EUR2023/MWh.

Leave-one-out deltas do not add up to the total improvement, since the
developments interact.

Run from the repo root (GAMS_SYSTEM_DIR comes from .env):
    pixi run python analysis/backcast_ablation_tornado.py
"""

import warnings
from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as Path_
from pybalmorel.backcasting.__main__ import (
    get_and_format_balmorel,
    get_and_format_entsoe,
    join_generation,
    join_hourly,
)
from pybalmorel.backcasting.calendar import backcast_hours

RUNS = ["ref", "hydro", "nuclear", "demand", "mustrun", "vre"]
LABELS = {
    "hydro": "Hydro FLH (absolute)",
    "nuclear": "Nuclear availability",
    "demand": "Demand (ENTSO-E)",
    "mustrun": "Must-run floor",
    "vre": "VRE scaling (ENTSO-E)",
}
METRICS = {
    "generation_twh": ("Generation", "Σ|B − E| over country × category", "TWh"),
    "load_twh": ("Load", "Σ|B − E| over countries", "TWh"),
    "price_mae": ("Price level", "hourly MAE", "€/MWh"),
    "price_spread": ("Price shape", "mean |σ(B) − σ(E)| per country", "€/MWh"),
}

# Catppuccin Mocha text/grid tokens; series pair validated with the dataviz
# validator in dark mode against the Mocha base (#1e1e2e)
TEXT = "#cdd6f4"
TEXT_MUTED = "#a6adc8"
GRID = "#45475a"
BASELINE = "#7f849c"
HELPED = "#5b8ae0"
HURT = "#d9773f"
FONT_DIR = Path.home() / ".local/share/fonts/Inter/extras/ttf"  # not on matplotlib's search path


def set_font():
    for ttf in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(
        (f for f in ("Inter", "Noto Sans") if f in available), "DejaVu Sans"
    )


def scores(entsoe, balmorel, year: int, regions: dict[str, set]) -> tuple[dict, pd.DataFrame]:
    """Score one run against ENTSO-E. Returns the metric scores and the
    per-category generation error in annual TWh."""
    e_load, e_price, e_gen = entsoe
    b_load, b_price, b_gen = balmorel
    n_year = len(backcast_hours(year))

    with warnings.catch_warnings():
        # join_hourly warns for every region, since F has 1/7 of the hours
        warnings.simplefilter("ignore", UserWarning)
        load = join_hourly(e_load, b_load, year, "load").dropna()
        price = join_hourly(e_price, b_price, year, "price").dropna()

    load = load[load.index.get_level_values("Region").isin(regions["load"])]
    price = price[price.index.get_level_values("Region").isin(regions["price"])]

    # Annual equivalent per region: mean hourly MW over the shared hours x year length
    load_twh = load.groupby(level="Region").mean() * n_year / 1e6
    out = {"load_twh": (load_twh.BALMOREL - load_twh.ENTSOE).abs().sum()}

    out["price_mae"] = (price.BALMOREL - price.ENTSOE).abs().mean()
    std = price.groupby(level="Region").std()
    out["price_spread"] = (std.BALMOREL - std.ENTSOE).abs().mean()

    # Generation at F's hours only, so Balmorel's unsolved hours aren't read as 0
    f_hours = set(b_load.Time)
    gen = join_generation(e_gen, b_gen, regions["generation"], year).reset_index()
    gen = gen[gen.Time.isin(f_hours)]
    n_hours = gen.groupby("Region").Time.nunique()
    gen_twh = gen.groupby(["Region", "Technology"])[["ENTSOE", "BALMOREL"]].sum()
    gen_twh = gen_twh.div(n_hours, axis=0, level="Region") * n_year / 1e6
    gen_twh["AbsError"] = (gen_twh.BALMOREL - gen_twh.ENTSOE).abs()
    out["generation_twh"] = gen_twh.AbsError.sum()

    return out, gen_twh.reset_index()


def rounded_barh(ax, y: float, width: float, height: float, color: str, radius_pt: float = 3):
    """Horizontal bar from 0 to `width`, rounded at the data end only.
    Call after the axis limits and figure layout are fixed."""
    if width == 0:
        return
    # Corner radius in data units, so the corners stay circular on screen
    px_per_pt = ax.figure.dpi / 72
    sx, sy = np.abs(ax.transData.transform([1, 1]) - ax.transData.transform([0, 0]))
    r_x = min(radius_pt * px_per_pt / sx, abs(width))
    r_y = min(radius_pt * px_per_pt / sy, height / 2)
    s = np.sign(width)
    y0, y1 = y - height / 2, y + height / 2
    vertices = [
        (0, y0), (width - s * r_x, y0),
        (width, y0), (width, y0 + r_y),  # rounded data-end corner
        (width, y1 - r_y),
        (width, y1), (width - s * r_x, y1),  # rounded data-end corner
        (0, y1), (0, y0),
    ]
    codes = [
        Path_.MOVETO, Path_.LINETO,
        Path_.CURVE3, Path_.CURVE3,
        Path_.LINETO,
        Path_.CURVE3, Path_.CURVE3,
        Path_.LINETO, Path_.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(Path_(vertices, codes), facecolor=color, edgecolor="none", zorder=3))


def tornado_panel(ax, delta: pd.Series, ref_score: float, metric: str, show_labels: bool):
    """One tornado panel: rows in `delta`'s order, top to bottom."""
    title, desc, unit = METRICS[metric]
    y = np.arange(len(delta))[::-1]
    # Only extend past zero on a side that has bars, with room for the value labels
    lo, hi = min(0, delta.min()), max(0, delta.max())
    span = max(hi - lo, 1e-9)
    ax.set_xlim(lo - (0.28 if lo < 0 else 0.04) * span, hi + (0.28 if hi > 0 else 0.04) * span)
    ax.set_ylim(-0.6, len(delta) - 0.4)

    ax.axvline(0, color=BASELINE, lw=0.8, zorder=2)
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(axis="both", length=0, colors=TEXT_MUTED, labelsize=7)
    # With sharey the labels are shared too, so hide them rather than clearing them
    ax.set_yticks(y, [LABELS[k] for k in delta.index], color=TEXT, fontsize=7.5)
    ax.tick_params(axis="y", labelleft=show_labels)
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    ax.set_title(
        f"{title}  ·  {unit}", loc="left", color=TEXT, fontsize=8.5, fontweight="semibold", pad=11
    )
    ax.text(
        0, 1.015, f"{desc}; ref error {ref_score:,.1f}",
        transform=ax.transAxes, color=TEXT_MUTED, fontsize=6.5, va="bottom",
    )

    ax._tornado = (y, delta, span)  # drawn by draw_bars once the layout is fixed


def draw_bars(ax):
    y, delta, span = ax._tornado
    for yi, d in zip(y, delta):
        rounded_barh(ax, yi, d, 0.5, HELPED if d > 0 else HURT)
        fmt = (f"{d:+.0f}" if abs(d) >= 10 else f"{d:+.1f}").replace("-", "−")
        pad = span * 0.025
        ax.text(
            d + (pad if d >= 0 else -pad), yi, fmt,
            ha="left" if d >= 0 else "right", va="center", color=TEXT, fontsize=6.5, zorder=4,
        )


def legend(fig, y: float):
    handles = [
        Patch(facecolor=HELPED, label="development improved the fit (error rises without it)"),
        Patch(facecolor=HURT, label="development worsened the fit"),
    ]
    fig.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.5, y), ncol=2, frameon=False,
        fontsize=6.5, labelcolor=TEXT_MUTED, handlelength=1.0, handleheight=0.8, columnspacing=1.6,
    )


def footnote(fig, y: float):
    fig.text(
        0.5, y,
        "B = Balmorel F2023, E = ENTSO-E 2023. Bar = error without the development − error with "
        "all of them (ref). Leave-one-out: the bars do not add up.",
        ha="center", va="top", color=TEXT_MUTED, fontsize=5.5,
    )


def save(fig, path: Path):
    for ext in ("pdf", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), transparent=True, dpi=300, bbox_inches="tight")
    print("saved", path.with_suffix(".pdf"), "+ .png")


@click.command()
@click.option("--entsoe-path", default="backcast/entsoedata", show_default=True)
@click.option("--year", default=2023, show_default=True)
@click.option("--overwrite", is_flag=True, help="Reread the MainResults GDXs")
@click.option("--plot-path", default="analysis/plots", show_default=True)
@click.option("--output-path", default="analysis/output", show_default=True)
def main(entsoe_path, year, overwrite, plot_path, output_path):
    plot_path, output_path = Path(plot_path), Path(output_path)
    set_font()

    e_load, e_price, e_gen, e_load_r, e_price_r, e_gen_r = get_and_format_entsoe(
        entsoe_path, year, "mean"
    )
    runs = {}
    for run in RUNS:
        b_load, b_price, b_gen, _, b_load_r, b_price_r, b_gen_r, _ = get_and_format_balmorel(
            f"backcast_abl_{run}_F{year}", f"backcast_abl_{run}", year, "mean", overwrite,
            allow_unmapped=True,  # CONDENSING - PEAT, 0.00 TWh
        )
        runs[run] = ((b_load, b_price, b_gen), {"load": b_load_r, "price": b_price_r, "generation": b_gen_r})

    # Same regions for every run, so the deltas only reflect the model change
    regions = {}
    for key, e_regions in (("load", e_load_r), ("price", e_price_r), ("generation", e_gen_r)):
        per_run = [r[1][key] for r in runs.values()]
        if any(s != per_run[0] for s in per_run):
            warnings.warn(f"{key} regions differ between runs, using the intersection")
        regions[key] = set(e_regions).intersection(*per_run)
        print(f"{key}: {len(regions[key])} regions")

    score_rows, gen_rows = {}, []
    for run, (balmorel, _) in runs.items():
        score_rows[run], gen = scores((e_load, e_price, e_gen), balmorel, year, regions)
        gen_rows.append(gen.assign(Run=run))
    score = pd.DataFrame(score_rows).T[list(METRICS)]
    delta = score.drop("ref") - score.loc["ref"]

    output_path.mkdir(parents=True, exist_ok=True)
    pd.concat({"score": score, "delta_vs_ref": delta}, axis=1).to_csv(
        output_path / f"backcast_ablation_scores_F{year}.csv"
    )
    gen_cat = (
        pd.concat(gen_rows)
        .groupby(["Run", "Technology"])[["ENTSOE", "BALMOREL", "AbsError"]]
        .sum()
        .round(2)
    )
    gen_cat.to_csv(output_path / f"backcast_ablation_generation_by_category_F{year}.csv")
    print(score.round(2).to_string(), "\n")
    print("delta vs ref (positive = development helped)")
    print(delta.round(2).to_string())

    plot_path.mkdir(parents=True, exist_ok=True)

    # Combined 2x2, rows in one order (by generation delta) so they line up
    order = delta.generation_twh.sort_values(ascending=False).index
    fig, axes = plt.subplots(2, 2, figsize=(6.0, 3.6), sharey=True)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.86, bottom=0.08, hspace=0.62, wspace=0.12)
    for ax, metric in zip(axes.flat, METRICS):
        tornado_panel(ax, delta.loc[order, metric], score.loc["ref", metric], metric,
                      show_labels=ax in axes[:, 0])
    for ax in axes.flat:
        draw_bars(ax)
    legend(fig, 0.935)
    footnote(fig, 0.0)
    save(fig, plot_path / f"backcast_ablation_tornado_F{year}")
    plt.close(fig)

    # One figure per metric, each sorted by its own |delta|
    for metric in METRICS:
        d = delta[metric].reindex(delta[metric].abs().sort_values(ascending=False).index)
        fig, ax = plt.subplots(figsize=(6.0, 2.2))
        fig.subplots_adjust(left=0.22, right=0.97, top=0.74, bottom=0.1)
        tornado_panel(ax, d, score.loc["ref", metric], metric, show_labels=True)
        draw_bars(ax)
        legend(fig, 0.88)
        footnote(fig, -0.02)
        save(fig, plot_path / f"backcast_ablation_tornado_{metric}_F{year}")
        plt.close(fig)


if __name__ == "__main__":
    main()
