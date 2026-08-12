"""
Capex/Opex Cost Splicing

A rolling/fullyear scenario's own OBJ_YCR only carries operational costs -
capacity investment costs live in its matching investment-run scenario
(MainResults_%scenario%_INV.gdx). combine_capex_opex splices the two into
one system-cost breakdown per scenario, for callers (analyse.py's
combined-costs command, and GREAT's category-cost aggregation) that need
total system cost rather than just operational cost.

Created on 11.08.2026
@author: Mathias Berg Rosendal
         PostDoc at DTU Management (Energy Economics & Modelling)
"""
# ------------------------------- #
#        0. Script Settings       #
# ------------------------------- #

import re

import pandas as pd

CAPEX_CATEGORIES = [
    "GENERATION_CAPITAL_COSTS",
    "GENERATION_FIXED_COSTS",
    "TRANSMISSION_CAPITAL_COSTS",
    "H2_TRANSMISSION_CAPITAL_COSTS",
]

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


def combine_capex_opex(
    df: pd.DataFrame,
    scenario_names: list,
    scenarios: list,
    capex_categories: list = CAPEX_CATEGORIES,
) -> tuple[pd.DataFrame, list]:
    """Splice each R20YY-suffixed scenario's operational OBJ_YCR rows with
    its matching _INV scenario's capex rows (``capex_categories`` - generation
    and transmission capital/fixed costs).

    Returns (combined, missing): combined is the row-level (not pivoted)
    spliced OBJ_YCR data for every scenario that had both an operational and
    an investment-run MainResults file; missing is whichever requested
    scenario names didn't (no matching _INV, or absent entirely).
    """
    is_capex = df["Category"].isin(capex_categories)

    missing = []
    parts = []
    for sc in scenarios:
        inv_scenario = re.sub(r"R20(30|40|50)$", "INV", sc)
        if sc not in scenario_names or inv_scenario not in scenario_names:
            missing.append(sc)
            continue

        capacity = df[(df["Scenario"] == inv_scenario) & is_capex].assign(Scenario=sc)
        operational = df[(df["Scenario"] == sc) & ~is_capex]
        parts.append(pd.concat([capacity, operational]))

    combined = pd.concat(parts) if parts else df.iloc[0:0]
    return combined, missing
