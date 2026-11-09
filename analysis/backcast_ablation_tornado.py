"""Tornado plots of the leave-one-out backcast ablation (F2023), against the ref run.

Each ablation run `backcast_abl_<name>` is the F2023 backcast with one
development removed; `backcast_abl_ref` has all of them and is the baseline
here (the comparison of ref with ENTSO-E is a separate slide). Every bar is
signed: run without the development - ref, so 0 means "same as ref".

Panels:
- Generation: annual TWh per technology category, summed over all regions,
  stacked so the bar shows what replaces what.
- Load: annual TWh per country, stacked (the net sum hides how much load the
  demand development moves between countries).
- Price level: mean hourly price difference over regions and hours, EUR2023/MWh.
- Price shape: mean over regions of std(run) - std(ref), EUR2023/MWh.

F only solves every 7th hour; both sides have the same hours, and annual TWh
is mean hourly MW x the 8736-hour year.

Leave-one-out deltas do not add up to the total effect, since the
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
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as Path_
from pybalmorel.backcasting.__main__ import get_and_format_balmorel
from pybalmorel.backcasting.calendar import backcast_hours

ABLATIONS = ["hydro", "nuclear", "demand", "mustrun", "vre"]
LABELS = {
    "hydro": "Hydro FLH (absolute)",
    "nuclear": "Nuclear availability",
    "demand": "Demand (ENTSO-E)",
    "mustrun": "Must-run floor",
    "vre": "VRE scaling (ENTSO-E)",
}
PANELS = {
    "generation": ("Generation", "TWh", "per technology, all regions"),
    "load": ("Load", "TWh", "per country"),
    "price_level": ("Price level", "€/MWh", "mean over countries and hours"),
    "price_shape": ("Price shape", "€/MWh", "σ of hourly prices, mean over countries"),
}

# pybalmorel category -> plotted category. Order = stack order outward from 0,
# the order the palette below was validated in (adjacent pairs, dark mode)
TECHNOLOGIES = {
    "Hydro": "#3987e5",
    "Fossil gas": "#d95926",
    "Wind": "#199e70",
    "Solar": "#c98500",
    "Coal & lignite": "#d55181",
    "Biomass": "#008300",
    "Nuclear": "#9085e9",
    "Other": "#7f849c",  # neutral fold: oil, storage, waste, backup, unmapped
}
CATEGORY = {
    "Hydro": "Hydro",
    "Fossil Gas": "Fossil gas",
    "Wind": "Wind",
    "Solar": "Solar",
    "Fossil Solid": "Coal & lignite",
    "Biomass & Bioenergy": "Biomass",
    "Nuclear": "Nuclear",
}

# Catppuccin Mocha tokens
TEXT = "#cdd6f4"
TEXT_MUTED = "#a6adc8"
GRID = "#45475a"
BASELINE = "#7f849c"
SURFACE = "#1e1e2e"
NEUTRAL = "#bac2de"  # single-series bars (load, prices), lighter than the "Other" grey
FONT_DIR = Path.home() / ".local/share/fonts/Inter/extras/ttf"  # not on matplotlib's search path

MIN_SEGMENT = 1.0  # TWh; smaller technology segments are not drawn
GAP_PT = 0.6  # gap between stacked segments
RADIUS_PT = 3


def set_font():
    for ttf in FONT_DIR.glob("Inter-*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    available = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams["font.family"] = next(
        (f for f in ("Inter", "Noto Sans") if f in available), "DejaVu Sans"
    )


def load_run(run: str, year: int, overwrite: bool):
    load, price, gen, *_ = get_and_format_balmorel(
        f"backcast_abl_{run}_F{year}", f"backcast_abl_{run}", year, "mean", overwrite,
        allow_unmapped=True,  # CONDENSING - PEAT, 0.00 TWh
    )
    return load, price, gen


def annual_twh(df: pd.DataFrame, keys: list[str], n_hours: int, n_year: int) -> pd.Series:
    """Annual TWh from hourly MW at F's hours (MainResults leaves out zeros,
    so divide by the solved hours, not the rows)."""
    return df.groupby(keys).Value.sum() / n_hours * n_year / 1e6


def deltas(run, ref, year: int) -> dict:
    """Signed run - ref for every panel."""
    (load, price, gen), (r_load, r_price, r_gen) = run, ref
    hours = set(load.Time)
    if hours != set(r_load.Time):
        raise ValueError("The run and ref solved different hours")
    n_hours, n_year = len(hours), len(backcast_hours(year))

    def per_tech(g):
        g = g.assign(Technology=g.Technology.map(CATEGORY).fillna("Other"))
        return annual_twh(g, ["Technology"], n_hours, n_year)

    gen_d = per_tech(gen).sub(per_tech(r_gen), fill_value=0).reindex(TECHNOLOGIES, fill_value=0)
    load_d = annual_twh(load, ["Region"], n_hours, n_year).sub(
        annual_twh(r_load, ["Region"], n_hours, n_year), fill_value=0
    )

    p = price.set_index(["Region", "Time"]).Value
    r_p = r_price.set_index(["Region", "Time"]).Value
    p, r_p = p.align(r_p, join="inner")
    std_d = p.groupby(level="Region").std() - r_p.groupby(level="Region").std()

    return {
        "generation": gen_d,
        "load": load_d,
        "price_level": (p - r_p).mean(),
        "price_shape": std_d.mean(),
    }


# ------------------------------- #
#            Drawing              #
# ------------------------------- #


def pt_to_data(ax, pt: float) -> tuple[float, float]:
    """`pt` points in x and y data units (call once the layout is fixed)."""
    px = pt * ax.figure.dpi / 72
    sx, sy = np.abs(ax.transData.transform([1, 1]) - ax.transData.transform([0, 0]))
    return px / sx, px / sy


def segment(ax, y: float, x0: float, x1: float, height: float, color: str, round_end: bool):
    """Horizontal bar from x0 (nearer 0) to x1, rounded at x1 if `round_end`."""
    width = x1 - x0
    if width == 0:
        return
    r_x, r_y = pt_to_data(ax, RADIUS_PT) if round_end else (0, 0)
    r_x, r_y = min(r_x, abs(width)), min(r_y, height / 2)
    s = np.sign(width)
    y0, y1 = y - height / 2, y + height / 2
    vertices = [
        (x0, y0), (x1 - s * r_x, y0),
        (x1, y0), (x1, y0 + r_y),
        (x1, y1 - r_y),
        (x1, y1), (x1 - s * r_x, y1),
        (x0, y1), (x0, y0),
    ]
    codes = [
        Path_.MOVETO, Path_.LINETO,
        Path_.CURVE3, Path_.CURVE3,
        Path_.LINETO,
        Path_.CURVE3, Path_.CURVE3,
        Path_.LINETO, Path_.CLOSEPOLY,
    ]
    ax.add_patch(PathPatch(Path_(vertices, codes), facecolor=color, edgecolor="none", zorder=3))


def ink_on(fill: str) -> str:
    """Near-black or white, whichever reads better on `fill`."""
    def lum(c):
        c = np.array(to_rgb(c))
        c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    on_dark = (lum("#ffffff") + 0.05) / (lum(fill) + 0.05)
    on_light = (lum(fill) + 0.05) / (lum(SURFACE) + 0.05)
    return "#ffffff" if on_dark > on_light else SURFACE


def fmt(v: float) -> str:
    return (f"{v:+.0f}" if abs(v) >= 10 else f"{v:+.1f}").replace("-", "−")


def label_inside(ax, x0: float, x1: float, y: float, texts: list[str], fill: str):
    """Centre the first of `texts` that fits in the segment, or none."""
    renderer = ax.figure.canvas.get_renderer()
    seg_px = abs(ax.transData.transform([x1, 0])[0] - ax.transData.transform([x0, 0])[0])
    for text in texts:
        t = ax.text((x0 + x1) / 2, y, text, ha="center", va="center", fontsize=5.5,
                    color=ink_on(fill), zorder=4)
        if t.get_window_extent(renderer).width + 4 * ax.figure.dpi / 72 <= seg_px:
            return
        t.remove()


def stacked_row(ax, y: float, parts: pd.Series, colors: dict, labeler, height=0.5):
    """Diverging stacked bar: positive parts right of 0, negative left, each
    side in `parts`' order outward from 0."""
    gap, _ = pt_to_data(ax, GAP_PT)
    for side in (parts[parts > 0], parts[parts < 0]):
        edge = 0.0
        for i, (key, value) in enumerate(side.items()):
            x0 = edge + (np.sign(value) * gap / 2 if edge else 0)
            x1 = edge + value
            outer = i == len(side) - 1
            segment(ax, y, x0, x1 - (0 if outer else np.sign(value) * gap / 2), height,
                    colors[key], round_end=outer)
            label_inside(ax, x0, x1, y, labeler(key, value), colors[key])
            edge = x1


def setup_panel(ax, panel: str, rows: list[str], xlim: tuple[float, float], show_labels: bool):
    title, unit, desc = PANELS[panel]
    y = np.arange(len(rows))[::-1]
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.axvline(0, color=BASELINE, lw=0.8, zorder=2)
    ax.grid(axis="x", color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(axis="both", length=0, colors=TEXT_MUTED, labelsize=7)
    ax.set_yticks(y, [LABELS[r] for r in rows], color=TEXT, fontsize=7.5)
    ax.tick_params(axis="y", labelleft=show_labels)
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:+g}".replace("-", "−") if v else "0")
    ax.set_title(f"{title}  ·  {unit}", loc="left", color=TEXT, fontsize=8.5,
                 fontweight="semibold", pad=11)
    ax.text(0, 1.015, desc, transform=ax.transAxes, color=TEXT_MUTED, fontsize=6.5, va="bottom")
    return y


def draw_panel(ax, panel: str, rows: list[str], d: dict):
    """Draw the bars of one panel (after the layout is fixed)."""
    y = np.arange(len(rows))[::-1]
    for yi, run in zip(y, rows):
        if panel == "generation":
            parts = d[run]["generation"]
            parts = parts[parts.abs() >= MIN_SEGMENT]
            stacked_row(ax, yi, parts, TECHNOLOGIES, lambda k, v: [fmt(v)])
        elif panel == "load":
            # Largest countries nearest 0; the small ones fold into one unlabelled segment
            parts = d[run]["load"]
            small = parts.abs() < 0.03 * np.diff(ax.get_xlim())[0]
            parts = parts[~small].reindex(parts[~small].abs().sort_values(ascending=False).index)
            folded = pd.Series({
                " +": d[run]["load"][small & (d[run]["load"] > 0)].sum(),
                " −": d[run]["load"][small & (d[run]["load"] < 0)].sum(),
            })
            parts = pd.concat([parts, folded[folded.abs() > 0]])
            stacked_row(ax, yi, parts, {k: NEUTRAL for k in parts.index},
                        lambda k, v: [] if k.startswith(" ") else [f"{k} {fmt(v)}", k])
        else:
            v = d[run][panel]
            segment(ax, yi, 0, v, 0.5, NEUTRAL, round_end=True)
            pad = 0.02 * np.diff(ax.get_xlim())[0]
            ax.text(v + (pad if v >= 0 else -pad), yi, fmt(v), ha="left" if v >= 0 else "right",
                    va="center", color=TEXT, fontsize=6.5, zorder=4)


def shared_xlim(lo: float, hi: float, pad: float = 0.04):
    span = hi - lo
    return lo - pad * span, hi + pad * span


def tech_legend(fig, y: float):
    """Technology legend, tagged so the load panel's bars don't read as 'Other'."""
    handles = [Patch(facecolor=c, label=t) for t, c in TECHNOLOGIES.items()]
    legend = fig.legend(
        handles=handles, loc="lower center", bbox_to_anchor=(0.55, y), ncol=len(handles),
        frameon=False, fontsize=6.5, labelcolor=TEXT_MUTED, handlelength=1.0, handleheight=0.8,
        columnspacing=1.2, handletextpad=0.5,
    )
    fig.canvas.draw()
    box = legend.get_window_extent().transformed(fig.transFigure.inverted())
    fig.text(box.x0, (box.y0 + box.y1) / 2, "Generation:", ha="right", va="center",
             color=TEXT, fontsize=6.5, fontweight="semibold")


def footnote(fig, y: float):
    fig.text(
        0.5, y,
        "Each bar: Balmorel F2023 without one development − F2023 ref (all developments); "
        "0 = same as ref. Leave-one-out: the rows do not add up.",
        ha="center", va="top", color=TEXT_MUTED, fontsize=5.5,
    )


def save(fig, path: Path):
    for ext in ("pdf", "png"):
        fig.savefig(path.with_suffix(f".{ext}"), transparent=True, dpi=300, bbox_inches="tight")
    print("saved", path.with_suffix(".pdf"), "+ .png")


@click.command()
@click.option("--year", default=2023, show_default=True)
@click.option("--overwrite", is_flag=True, help="Reread the MainResults GDXs")
@click.option("--plot-path", default="analysis/plots", show_default=True)
@click.option("--output-path", default="analysis/output", show_default=True)
def main(year, overwrite, plot_path, output_path):
    plot_path, output_path = Path(plot_path), Path(output_path)
    set_font()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # Unmapped CONDENSING - PEAT, 0.00 TWh
        ref = load_run("ref", year, overwrite)
        d = {run: deltas(load_run(run, year, overwrite), ref, year) for run in ABLATIONS}

    output_path.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame({
        run: pd.concat([
            v["generation"].add_prefix("generation: "),
            pd.Series({
                "load net": v["load"].sum(),
                "load Σ|Δ| over countries": v["load"].abs().sum(),
                "price level": v["price_level"],
                "price shape": v["price_shape"],
            }),
        ])
        for run, v in d.items()
    }).T
    table.round(2).to_csv(output_path / f"backcast_ablation_vs_ref_F{year}.csv")
    pd.DataFrame({run: v["load"] for run, v in d.items()}).round(2).to_csv(
        output_path / f"backcast_ablation_vs_ref_load_by_country_F{year}.csv"
    )
    print("run − ref\n", table.round(1).T.to_string())

    # Rows by how much generation moves, the same order in every panel
    rows = sorted(ABLATIONS, key=lambda r: -d[r]["generation"].abs().sum())

    # Same unit, same scale: generation with load, price level with price shape
    def side_sums(key):
        pos = [d[r][key].clip(lower=0).sum() for r in rows]
        neg = [d[r][key].clip(upper=0).sum() for r in rows]
        return min(neg), max(pos)

    g_lo, g_hi = side_sums("generation")
    l_lo, l_hi = side_sums("load")
    twh = shared_xlim(min(g_lo, l_lo), max(g_hi, l_hi))
    prices = [d[r][k] for r in rows for k in ("price_level", "price_shape")]
    eur = shared_xlim(min(0, *prices), max(0, *prices), pad=0.22)
    xlims = {"generation": twh, "load": twh, "price_level": eur, "price_shape": eur}

    plot_path.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(6.0, 3.6), sharey=True)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.86, bottom=0.08, hspace=0.62, wspace=0.12)
    for ax, panel in zip(axes.flat, PANELS):
        setup_panel(ax, panel, rows, xlims[panel], show_labels=ax in axes[:, 0])
    for ax, panel in zip(axes.flat, PANELS):
        draw_panel(ax, panel, rows, d)
    tech_legend(fig, 0.935)
    footnote(fig, 0.0)
    save(fig, plot_path / f"backcast_ablation_tornado_F{year}")
    plt.close(fig)

    # One figure per panel
    for panel in PANELS:
        fig, ax = plt.subplots(figsize=(6.0, 2.2))
        fig.subplots_adjust(left=0.22, right=0.97, top=0.74 if panel == "generation" else 0.8,
                            bottom=0.1)
        setup_panel(ax, panel, rows, xlims[panel], show_labels=True)
        draw_panel(ax, panel, rows, d)
        if panel == "generation":
            tech_legend(fig, 0.88)
        footnote(fig, -0.02)
        save(fig, plot_path / f"backcast_ablation_tornado_{panel}_F{year}")
        plt.close(fig)


if __name__ == "__main__":
    main()
