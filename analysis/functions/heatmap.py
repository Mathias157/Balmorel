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

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from decouple import config
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

    # Relative range per output: (max - min) / mean
    rel_range = (df_y.max() - df_y.min()) / df_y.mean()  # Series, index=outputs

    # Per-cell deviation from mean: (value - mean) / mean  (signed)
    rel_dev = (df_y - df_y.mean()) / df_y.mean()  # DataFrame, same shape as df_y

    return rel_dev, rel_range


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


# ------------------------------- #
#            2. Main              #
# ------------------------------- #


def main():
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

    scenarios = [
        "base_R2050",
        "DCN_R2050",
        "EVN_R2050",
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

    scenario_labels = {
        "base_R2050": "base",
        "DCN_R2050": "DCN",
        "EVN_R2050": "EVN",
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

    # Load results (change to MainResults if timeseries-heavy results are required?)
    model = Balmorel(
        "analysis/Balmorel",
        gams_system_directory=config("GAMS_SYSTEM_DIR"),  # pyright: ignore
    )
    model.collect_results()
    res = model.results

    # Compute once, reuse for all plots

    rel_dev, rel_range = compute_relative_importance(
        res=res,
        scenarios=scenarios,
        regions="all",
        year="2050",
        outputs=outputs,
        output_symbol=output_symbol,
        filters=filters,
    )

    fig_heat = plot_importance_heatmap(
        rel_dev,
        rel_range,
        title="Scenario Importance — relative deviation from mean",
        scenario_labels=scenario_labels,
    )
    fig_heat.savefig("test.png", dpi=300)


if __name__ == "__main__":
    main()
