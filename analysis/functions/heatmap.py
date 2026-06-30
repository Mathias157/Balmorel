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

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from pybalmorel import Balmorel

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #

param_labels = {
    "CO2_TAX": "CO2 Tax",
    "PV_INVC": "PV CAPEX",
    "ONS_WT_INVC": "Onshore Wind CAPEX",
    "OFF_WT_INVC": "Offshore Wind CAPEX",
    "H2_TRANS_INVC": "H2 Transmission CAPEX",
    "ELEC_TRANS_INVC": "Electricity Transmission CAPEX",
    "NATGAS_P": "Natural Gas Price",
    "EV_BEV_available": "EV BEV Availability",
    "V2G_EFF": "V2G Efficiency",
    "EV_CHARGE_CAP": "EV Charger Capacity",
    "ADOPTION_RATE_DR": "Demand Response Adoption Rate",
    "BATTERIES_OandM": "Battery OPEX",
    "BATTERIES_INVCOST0": "Battery CAPEX",
    "V2G_SHARE": "V2G Share",
    "DH2_DEMAND": "Hydrogen Demand",
    "H2S_INVC": "H2 Storage CAPEX",
    "HS_INVC": "Heat Storage CAPEX",
    "HP_INVC": "Heat Pump CAPEX",
    "H2_INVCOST0": "Electrolyser CAPEX",
}


def compute_relative_importance(
    res, scenarios, regions, year, outputs, output_symbol, filters
):

    # Build output matrix: rows=scenarios, cols=outputs
    df_y = {}
    for output in outputs:
        if regions != "all":
            df_out = res.get_result(output_symbol[output]).query(
                f'Year == "{year}" and Regions in {regions} and Scenario in {scenarios}'
            )
        else:
            df_out = res.get_result(output_symbol[output]).query(
                f'Year == "{year}" and Scenario in {scenarios}'
            )

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
):
    # rows=outputs, cols=scenarios (transposed for display)
    data = rel_dev.T  # shape: outputs × scenarios
    rows = data.index.tolist()  # outputs
    cols = data.columns.tolist()  # scenarios

    rows_display = [output_labels.get(r, r) if output_labels else r for r in rows]
    cols_display = [scenario_labels.get(c, c) if scenario_labels else c for c in cols]

    nrows, ncols = len(rows), len(cols)

    # Circle radius scaled by rel_range of that output row
    r_min, r_max = 0.08, 0.45
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
        "Production (TWh)",
        "Generation Capacity (GW)",
        "Storage power cap (GW)",
        # "Peak Generation Production",
        # "Elec Battery Production",
        # "Elec Battery Capacity",
        # "Demand Response Production",
        # "Thermal Storage Production",
        # "Hydro Production",
        # "H2 Storage",
        # "Elec PV Production",
        # "Elec ONSHORE Production",
        # "Elec OFFSHORE Production",
        # "Elec Transmission Flow",
        # "Elec Transmission Capacity",
        # "Heat Pump Capacity",
        # "Heat Pump Production",
        # "H2 Green Capacity",
        # "H2 Green Production",
        # "H2 Transmission Flow",
        # "H2 Transmission Capacity",
    ]

    output_symbol = {
        "Production (TWh)": "PRO_YCRAGF",
        "Generation Capacity (GW)": "G_CAP_YCRAF",
        "Storage power cap (GW)": "G_CAP_YCRAF",
    }

    filters = {
        "Generation Capacity": 'not Technology.str.contains("STORAGE")',
        "Storage power cap (GW)": 'Technology.str.contains("STORAGE")',
    }

    scenarios = [
        "EVN_INV",
        "HPN_INV",
        "TPN_INV",
        "ELN_INV",
        "HSNSSN_INV",
        "HSN_INV",
        "SSN_INV",
        "EIN_INV",
        "DCN_INV",
        "H2N_INV",
        "base_INV",
    ]

    # Load results (change to MainResults if timeseries-heavy results are required?)
    model = Balmorel("analysis/Balmorel", gams_system_directory="/opt/gams/53")
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
    )
    fig_heat.savefig("test.png")

    # Bar chart: one output at a time
    # fig_bar = plot_srcc_bars(rho_matrix, pval_matrix, output="V2G Production")
    # fig_bar.show()


if __name__ == "__main__":
    main()
