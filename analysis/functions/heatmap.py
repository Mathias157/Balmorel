"""
Heatmap of Results x Scenarios

Plots various results (rows) as a function of scenario (column)

Created on 23.06.2026
@author: Mathias Berg Rosendal
         PostDoc at DTU Management (Energy Economics & Modelling)
"""
# ------------------------------- #
#        0. Script Settings       #
# ------------------------------- #

import click
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from cmcrameri import cm as cmc
from decouple import config
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from pybalmorel import Balmorel

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


class CachedResults:
    def __init__(self, results):
        self.results = results

    def get_and_cache(self, symbol, base_query: str | None = None):
        if not hasattr(self, symbol):
            print(f"Loading {symbol} into cache...")
            df = self.results.get_result(symbol)
            if base_query:
                try:
                    df = df.query(base_query)
                except pd.errors.UndefinedVariableError:
                    df = df.query(base_query.replace("Year", "Y"))

            setattr(self, symbol, df)
        else:
            df = getattr(self, symbol)

        return df

    def clear_cache(self, symbol):
        try:
            print(f"Removing {symbol} from cache...")
            delattr(self, symbol)
        except AttributeError:
            print(symbol, "already deleted from cache")


def compute_relative_importance(
    res, scenarios, regions, year, outputs, output_symbol, filters
):
    # Prepare data
    cached_results = CachedResults(res)

    # Build output matrix: rows=scenarios, cols=outputs
    df_y = {}
    for i, output in enumerate(outputs):
        current_symbol = output_symbol[output]
        if regions != "all":
            df_out = cached_results.get_and_cache(
                current_symbol,
                f'Year == "{year}" and Regions in {regions} and Scenario in {scenarios}',
            )
        else:
            df_out = cached_results.get_and_cache(
                current_symbol, f'Year == "{year}" and Scenario in {scenarios}'
            )

        if current_symbol not in [output_symbol[output] for output in outputs[i + 1 :]]:
            cached_results.clear_cache(current_symbol)

        if output in filters:
            df_out = df_out.query(filters[output])

        df_out = df_out.groupby("Scenario", as_index=False)["Value"].sum()
        df_y[output] = df_out.set_index("Scenario")["Value"]

    df_y = pd.DataFrame(df_y)  # shape: (n_scenarios, n_outputs)
    df_y = df_y.reindex(scenarios)  # keep scenarios with no data as NaN rows

    return relative_deviation(df_y)


def relative_deviation(df_y):
    """rel_range: (max - min) / mean per output/region.
    rel_dev: per-cell (value - mean) / mean, signed."""
    rel_range = (df_y.max() - df_y.min()) / df_y.mean()  # Series, index=outputs
    rel_dev = (df_y - df_y.mean()) / df_y.mean()  # DataFrame, same shape as df_y

    return rel_dev, rel_range


def get_region_to_country(model, base_scenario="base"):
    """RRR -> CCC mapping. Loaded from the base scenario's .inc files only,
    since region-to-country assignment doesn't vary across scenarios."""
    if base_scenario not in model.input_data:
        model.load_incfiles(scenario=base_scenario)

    cccrrr = model.get_input("CCCRRR")
    countries_in_model = model.get_input("C").CCC.unique()
    cccrrr = cccrrr.query("CCC in @countries_in_model")

    return cccrrr.set_index("RRR")["CCC"].to_dict()


def compute_net_import(res, scenarios, year, region_to_country, missing_scenarios=None):
    df = res.get_result("X_FLOW_YCR")
    df = df.query("Year == @year and Scenario in @scenarios")
    country_of_to = df["To"].map(region_to_country)

    net_import = {}
    for region, country in region_to_country.items():
        imports = df[(df["To"] == region) & (df["Country"] != country)]
        exports = df[(df["From"] == region) & (country_of_to != country)]

        import_by_scenario = imports.groupby("Scenario")["Value"].sum()
        export_by_scenario = exports.groupby("Scenario")["Value"].sum()

        net_import[region] = import_by_scenario.reindex(
            scenarios, fill_value=0
        ) - export_by_scenario.reindex(scenarios, fill_value=0)

    df_y = pd.DataFrame(net_import)  # shape: (n_scenarios, n_regions)

    # Aggregate to country level: intra-country flows were never counted as
    # import/export above, so summing regions within a country is exact.
    df_y = df_y.T.groupby(df_y.columns.map(region_to_country)).sum().T

    # Scenarios with no MainResults file at all have no real data, so the
    # reindex fill above is a placeholder, not an actual zero net import.
    if missing_scenarios:
        df_y.loc[df_y.index.intersection(missing_scenarios)] = np.nan

    return df_y


def plot_importance_heatmap(
    rel_dev,  # DataFrame: scenarios × outputs
    rel_range,  # Series: outputs
    title="Scenario Importance Heatmap",
    output_labels=None,
    scenario_labels=None,
    value_annotate=False,
):
    # rows=outputs, cols=scenarios (transposed for display)
    data = rel_dev.T  # shape: outputs × scenarios
    rows = data.index.tolist()  # outputs
    cols = data.columns.tolist()  # scenarios

    rows_display = [output_labels.get(r, r) if output_labels else r for r in rows]
    cols_display = [scenario_labels.get(c, c) if scenario_labels else c for c in cols]

    nrows, ncols = len(rows), len(cols)

    # Circle radius scaled by rel_range of that output row
    r_min, r_max = 0.04, 0.45
    rng_min = rel_range.min()
    rng_max = rel_range.max()

    def row_radius(output, cell_rel_dev):
        """Max radius for this row set by rel_range; scale within row by abs(rel_dev)."""
        row_max_r = r_min + (rel_range[output] - rng_min) / (
            rng_max - rng_min + 1e-9
        ) * (r_max - r_min)
        row_dev_max = rel_dev[output].abs().max()
        if row_dev_max == 0:
            return r_min
        return r_min + (abs(cell_rel_dev) / row_dev_max) * (row_max_r - r_min)

    fig, ax = plt.subplots(figsize=(max(ncols * 0.9, 10), max(nrows * 0.9, 4)))

    for i, output in enumerate(rows):
        for j, scenario in enumerate(cols):
            x, y = j, i
            rect = Rectangle(
                (x - 0.5, y - 0.5), 1, 1, facecolor="white", edgecolor="none"
            )
            ax.add_patch(rect)

            val = data.loc[output, scenario]
            if pd.isna(val):
                grey = Rectangle(
                    (x - 0.5, y - 0.5),
                    1,
                    1,
                    facecolor="#D9D9D9",
                    edgecolor="none",
                    zorder=2,
                )
                ax.add_patch(grey)
            else:
                radius = row_radius(output, val)
                color = "#E78AC3" if val > 0 else "#F4A261"
                circ = Circle(
                    (x, y),
                    radius,
                    facecolor=color,
                    edgecolor="none",
                    alpha=0.9,
                    zorder=2,
                )
                ax.add_patch(circ)

            if value_annotate and val is not np.nan:
                ax.annotate(f"{val * 100:2.1f}", xy=(x, y))

    # Grid
    for j in range(ncols + 1):
        ax.plot([j - 0.5, j - 0.5], [-0.5, nrows - 0.5], color="black", lw=0.8)
    for i in range(nrows + 1):
        ax.plot([-0.5, ncols - 0.5], [i - 0.5, i - 0.5], color="black", lw=0.8)

    # Column labels (scenarios, angled)
    y_top_grid = -0.5
    y_label = -0.8
    incline_length = min(ncols * 0.5, 2.0)
    for j in range(ncols + 1):
        x = j - 0.5
        ax.plot([x, x], [y_top_grid, y_label], color="black", lw=0.8)
        ax.plot(
            [x, x + incline_length],
            [y_label, y_label - incline_length],
            color="black",
            lw=0.8,
        )
    for j, col in enumerate(cols_display):
        ax.text(
            j,
            y_label - 0.1,
            col,
            rotation=45,
            ha="left",
            va="top",
            rotation_mode="anchor",
            fontsize=9,
        )

    # Row labels (outputs)
    for i, row in enumerate(rows_display):
        ax.text(-0.7, i, row, ha="right", va="center", fontsize=10)

    ax.set_xlim(-1.5, ncols - 0.5)
    ax.set_ylim(nrows - 0.5, y_label - incline_length - 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=20)

    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Above mean",
            markerfacecolor="#E78AC3",
            markersize=14,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Below mean",
            markerfacecolor="#F4A261",
            markersize=14,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="No data",
            markerfacecolor="#D9D9D9",
            markersize=14,
            markeredgecolor="grey",
        ),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        ncol=3,
        fontsize=10,
        frameon=False,
    )

    plt.tight_layout()
    return fig


def plot_net_import_heatmap(
    df_y,  # DataFrame: scenarios × countries, absolute net import values
    title="Net Import Heatmap",
    scenario_labels=None,
    cmap=cmc.vik,
):
    data = df_y.T  # shape: countries × scenarios (rows=countries, cols=scenarios)
    rows = data.index.tolist()  # countries
    cols = data.columns.tolist()  # scenarios
    cols_display = [scenario_labels.get(c, c) if scenario_labels else c for c in cols]

    nrows, ncols = len(rows), len(cols)

    values = data.to_numpy(dtype=float)
    vmax = np.nanmax(np.abs(values))
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    cmap = cmap.copy()
    cmap.set_bad("#D9D9D9")
    masked = np.ma.masked_invalid(values)

    fig, ax = plt.subplots(figsize=(max(ncols * 0.7, 8), max(nrows * 0.35, 6)))
    mesh = ax.pcolormesh(
        masked, cmap=cmap, norm=norm, edgecolors="white", linewidth=0.5
    )

    ax.set_xticks(np.arange(ncols) + 0.5)
    ax.set_xticklabels(cols_display, rotation=45, ha="right")
    ax.set_yticks(np.arange(nrows) + 0.5)
    ax.set_yticklabels(rows)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=13, fontweight="bold", pad=20)

    cbar = fig.colorbar(mesh, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Net import (TWh)")

    plt.tight_layout()
    return fig


# ------------------------------- #
#            2. Main              #
# ------------------------------- #

SCENARIOS = [
    "base_R2050",
    "DCN_R2050",
    "EVN_R2050",
    "VGN_R2050",
    "HPN_R2050",
    "TPN_R2050",
    "ELN_R2050",
    "HSNSSN_R2050",
    "HSN_R2050",
    "SSN_R2050",
    "EIN_R2050",
    "H2N_R2050",
    "ALLN_R2050",
]

SCENARIO_LABELS = {
    "base_R2050": "base",
    "DCN_R2050": "DCN",
    "EVN_R2050": "EVN",
    "VGN_R2050": "VGN",
    "HPN_R2050": "HPN",
    "TPN_R2050": "TPN",
    "ELN_R2050": "ELN",
    "HSNSSN_R2050": "HSNSSN",
    "HSN_R2050": "HSN",
    "SSN_R2050": "SSN",
    "EIN_R2050": "EIN",
    "H2N_R2050": "H2N",
    "ALLN_R2050": "ALLN",
}


def load_balmorel_model():
    model = Balmorel(
        "analysis/Balmorel",
        gams_system_directory=config("GAMS_SYSTEM_DIR"),  # pyright: ignore
    )
    model.collect_results()
    return model


@click.group()
@click.option("--year", default="2050", help="Year to plot")
@click.option("--dark-style", is_flag=True, required=False, help="Dark plot style")
@click.pass_context
def cli(ctx, year: str, dark_style: bool):
    ctx.ensure_object(dict)
    ctx.obj["year"] = year
    ctx.obj["dark_style"] = dark_style

    if dark_style:
        plt.style.use("dark_background")


@cli.command("scenario-comparison")
@click.pass_context
def scenario_comparison(ctx):
    year = ctx.obj["year"]
    facecolor = "none" if ctx.obj["dark_style"] else "white"

    outputs = [
        "Production",
        "Generation Capacity",
        "Storage Power Capacity",
        "Peak Generation Production",
        "Elec. Battery Production",
        "Elec. Battery Capacity",
        "Demand Response Use",
        "Thermal Storage Production",
        "Hydro Production",
        "H2 Storage Production",
        "Elec. PV Production",
        "Elec. Onshore Wind Production",
        "Elec. Offshore Wind Production",
        "Elec. Transmission Flow",
        "Elec. Transmission Capacity",
        "Heat Pump Capacity",
        "Heat Pump Production",
        "H2 Green Capacity",
        "H2 Green Production",
        "H2 Transmission Flow",
        "H2 Transmission Capacity",
    ]

    output_symbol = {
        "Production": "PRO_YCRAGF",
        "Generation Capacity": "G_CAP_YCRAF",
        "Storage Power Capacity": "G_CAP_YCRAF",
        "Peak Generation Production": "PRO_YCRAGF",
        "Elec. Battery Production": "G_CAP_YCRAF",
        "Elec. Battery Capacity": "G_CAP_YCRAF",
        "Demand Response Use": "DR_FLEX_Y",
        "Thermal Storage Production": "PRO_YCRAGF",
        "Hydro Production": "PRO_YCRAGF",
        "H2 Storage Production": "PRO_YCRAGF",
        "Elec. PV Production": "PRO_YCRAGF",
        "Elec. Onshore Wind Production": "PRO_YCRAGF",
        "Elec. Offshore Wind Production": "PRO_YCRAGF",
        "Elec. Transmission Flow": "X_FLOW_YCR",
        "Elec. Transmission Capacity": "X_CAP_YCR",
        "Heat Pump Capacity": "G_CAP_YCRAF",
        "Heat Pump Production": "PRO_YCRAGF",
        "H2 Green Capacity": "G_CAP_YCRAF",
        "H2 Green Production": "PRO_YCRAGF",
        "H2 Transmission Flow": "XH2_FLOW_YCR",
        "H2 Transmission Capacity": "XH2_CAP_YCR",
    }

    filters = {
        "Generation Capacity": 'not Technology.str.contains("STORAGE")',
        "Storage Power Capacity": 'Technology.str.contains("STORAGE")',
        "Elec. Battery Capacity": 'Generation.str.contains("ELEC_BAT")',
        "Peak Generation Production": 'Generation.str.contains("BACKUP")',
        "Elec. Battery Production": 'Generation.str.contains("ELEC_BAT")',
        "Thermal Storage Production": 'Technology.str.contains("STORAGE") and Commodity == "HEAT"',
        "Hydro Production": 'Technology.str.contains("HYDRO")',
        "H2 Storage Production": 'Technology == "H2-STORAGE"',
        "Elec. PV Production": 'Technology == "SOLAR-PV"',
        "Elec. Onshore Wind Production": 'Technology == "WIND-ON"',
        "Elec. Offshore Wind Production": 'Technology == "WIND-OFF"',
        "Heat Pump Capacity": 'Generation.str.contains("HP_ELEC")',
        "Heat Pump Production": 'Generation.str.contains("HP_ELEC")',
        "H2 Green Capacity": 'Technology == "ELECTROLYZER"',
        "H2 Green Production": 'Technology == "ELECTROLYZER"',
    }

    # Load results (change to MainResults if timeseries-heavy results are required?)
    model = load_balmorel_model()
    res = model.results

    rel_dev, rel_range = compute_relative_importance(
        res=res,
        scenarios=SCENARIOS,
        regions="all",
        year=year,
        outputs=outputs,
        output_symbol=output_symbol,
        filters=filters,
    )

    fig_heat = plot_importance_heatmap(
        rel_dev,
        rel_range,
        title="Scenario Importance — relative deviation from mean",
        scenario_labels=SCENARIO_LABELS,
    )
    fig_heat.savefig(
        "analysis/Balmorel/analysis/plots/heatmap.png", dpi=300, facecolor=facecolor
    )


@cli.command("net-import")
@click.pass_context
def net_import(ctx):
    year = ctx.obj["year"]
    facecolor = "none" if ctx.obj["dark_style"] else "white"

    model = load_balmorel_model()
    res = model.results

    missing_scenarios = [s for s in SCENARIOS if s not in model.scenario_names]

    region_to_country = get_region_to_country(model)

    df_y = compute_net_import(
        res=res,
        scenarios=SCENARIOS,
        year=year,
        region_to_country=region_to_country,
        missing_scenarios=missing_scenarios,
    )

    fig_heat = plot_net_import_heatmap(
        df_y,
        title="Net Import per Country",
        scenario_labels=SCENARIO_LABELS,
    )
    fig_heat.savefig(
        "analysis/Balmorel/analysis/plots/net_import_heatmap.png",
        dpi=300,
        facecolor=facecolor,
    )


if __name__ == "__main__":
    cli()
