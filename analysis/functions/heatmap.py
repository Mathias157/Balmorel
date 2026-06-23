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
import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.lines import Line2D
from pybalmorel import Balmorel
from scipy import stats

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


# TODO: Generally: Parameters will be scenarios in my case, scenario-dimension
# should be deleted, and .get_results replaced with .get_result
def compute_srcc(res, scenarios, outputs, regions, year):

    # Build output matrix
    # TODO: Change this to MainResults result collection
    df_y = {}
    for output in outputs:
        if regions != "all":
            df_out = res.get_result(output).query(
                f'Year == "{year}" and Regions in {regions} and Scenario in {scenarios}'
            )
        else:
            df_out = res.get_result(output).query(
                f'Year == "{year}" and Scenario in {scenarios}'
            )

        df_out = df_out.groupby("Scenario", as_index=False)["Value"].sum()
        df_y[output] = df_out.set_index("Scenario")["Value"]

    df_y = pd.DataFrame(df_y)  # missing scenarios become NaN automatically

    # Compute SRCC — per-pair mask handles any remaining NaNs
    rho_matrix = pd.DataFrame(index=scenarios, columns=outputs, dtype=float)
    pval_matrix = pd.DataFrame(index=scenarios, columns=outputs, dtype=float)

    for scenario in scenarios:
        for output in outputs:
            mask = df_y[output].notna()
            if mask.sum() < 3:
                rho_matrix.loc[scenario, output] = float("nan")
                pval_matrix.loc[scenario, output] = float("nan")
                continue
            rho, pval = stats.spearmanr(df_y.loc[mask, output])
            rho_matrix.loc[scenario, output] = rho
            pval_matrix.loc[scenario, output] = pval

    return rho_matrix, pval_matrix


def plot_srcc_heatmap(
    rho_matrix,
    pval_matrix,
    alpha=0.1,
    min_rho=0.1,
    title="SRCC Heatmap",
    param_labels=None,
):

    # Transpose so outputs (originally columns) are rows, inputs (originally rows) are columns
    rho_matrix = rho_matrix.T
    pval_matrix = pval_matrix.T

    rho = rho_matrix.values.astype(float)
    pval = pval_matrix.values.astype(float)
    significant = (pval < alpha) & (np.abs(rho) >= min_rho)

    rows = rho_matrix.index.tolist()  # outputs
    cols = rho_matrix.columns.tolist()  # inputs

    # Rename inputs if param_labels provided
    if param_labels:
        cols = [param_labels.get(c, c) for c in cols]

    nrows, ncols = len(rows), len(cols)

    def scale_radius(r, rmin=0.08, rmax=0.45):
        actual_min = np.abs(rho[significant]).min()
        actual_max = np.abs(rho[significant]).max()
        return rmin + (abs(r) - actual_min) / (actual_max - actual_min) * (rmax - rmin)

    fig, ax = plt.subplots(figsize=(max(ncols * 0.9, 14), max(nrows * 0.9, 6)))

    # --- Draw cells ---
    for i in range(nrows):
        for j in range(ncols):
            x, y = j, i
            rect = Rectangle(
                (x - 0.5, y - 0.5), 1, 1, facecolor="white", edgecolor="none"
            )
            ax.add_patch(rect)
            if significant[i, j]:
                r = rho[i, j]
                radius = scale_radius(r)
                color = "#E78AC3" if r > 0 else "#F4A261"
                circ = Circle(
                    (x, y),
                    radius,
                    facecolor=color,
                    edgecolor="none",
                    alpha=0.9,
                    zorder=2,
                )
                ax.add_patch(circ)
                # font_color = "white" if abs(r) > 0.5 else "black"
                # ax.text(x, y, f"{r:.2f}", ha="center", va="center",
                #        fontsize=7, color=font_color, zorder=3)
            else:
                grey_rect = Rectangle(
                    (x - 0.5, y - 0.5),
                    1,
                    1,
                    facecolor="#D9D9D9",
                    edgecolor="none",
                    zorder=2,
                )
                ax.add_patch(grey_rect)

    # --- Grid lines ---
    for j in range(ncols + 1):
        ax.plot([j - 0.5, j - 0.5], [-0.5, nrows - 0.5], color="black", lw=0.8)
    for i in range(nrows + 1):
        ax.plot([-0.5, ncols - 0.5], [i - 0.5, i - 0.5], color="black", lw=0.8)

    # --- Column labels (inputs, angled with inclined extension lines) ---
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
    for j, col in enumerate(cols):
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

    # --- Row labels (outputs) ---
    for i, row in enumerate(rows):
        ax.text(-0.7, i, row, ha="right", va="center", fontsize=10)

    # --- Limits & appearance ---
    ax.set_xlim(-1.5, ncols - 0.5)
    ax.set_ylim(nrows - 0.5, y_label - incline_length - 0.5)
    ax.set_aspect("equal")
    ax.axis("off")

    # --- Title ---
    ax.set_title(title, fontsize=13, fontweight="bold", pad=20)

    # --- Legend ---
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Positive correlation (ρ > 0)",
            markerfacecolor="#E78AC3",
            markersize=14,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Negative correlation (ρ < 0)",
            markerfacecolor="#F4A261",
            markersize=14,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Not significant / weak",
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
        "PRO_YCRAGF"
        # "V2G Production",
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

    model = Balmorel("analysis/Balmorel", gams_system_directory="/opt/gams/53")
    model.collect_results()
    res = model.results

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

    # Compute once, reuse for all plots
    # TODO: Input res and parameters correctly
    rho_matrix, pval_matrix = compute_srcc(
        res=res,
        scenarios=scenarios,
        outputs=outputs,
        regions="all",
        year="2050",
    )

    # Heatmap: full overview
    rho_matrix.columns = rho_matrix.columns.map(lambda x: param_labels.get(x, x))
    pval_matrix.columns = pval_matrix.columns.map(lambda x: param_labels.get(x, x))
    fig_heat = plot_srcc_heatmap(
        rho_matrix,
        pval_matrix,
        title="SRCC — All scenarios vs Outputs",
        param_labels=param_labels,
    )
    fig_heat.show()
    fig_heat.savefig("test.png")

    # Bar chart: one output at a time
    # fig_bar = plot_srcc_bars(rho_matrix, pval_matrix, output="V2G Production")
    # fig_bar.show()


if __name__ == "__main__":
    main()
