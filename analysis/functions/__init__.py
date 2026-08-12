"""
Functions

Utility functions for analyses

Created on 20.03.2026
@author: Mathias Berg Rosendal
         PhD Student at DTU Management (Energy Economics & Modelling)
"""
# ------------------------------- #
#        0. Script Settings       #
# ------------------------------- #

from pathlib import Path
from pybalmorel import MainResults
import pandas as pd

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


def find_most_recent_result(sc_folder: str):
    """Find the most recent MainResults in a scenario/model folder"""

    path = Path(f"{sc_folder}/model")
    results = [p for p in path.iterdir() if "MainResults" in str(p)]
    mtimes = [modified.stat().st_mtime for modified in results]
    most_recent = mtimes.index(max(mtimes))
    path = Path(results[most_recent])
    print(f"\nMost recent results in {sc_folder}: {path.name}\n")

    return path.name, str(path.parent)


def find_result(sc_folder: str, scenario: str = ""):
    if scenario != "":
        # If input, choose inputted scenario
        path = Path(f"{sc_folder}/model/MainResults_{scenario}.gdx")
        file = path.name
        path = str(path.parent)
    else:
        # If nothing input, find most recent MainResults
        file, path = find_most_recent_result(sc_folder)

    res = MainResults(file, path)

    return res


def format_lole_ens_adequacy_results(df: pd.DataFrame):
    # Get method, resolution, year and runtype
    pattern = (
        r"([FR]20[345]0)"  # pattern that matches R or F and then 2030, 2040 or 2050
    )
    df["ShortSC"] = df.Scenario.str.replace("_" + pattern, "", regex=True)
    year = df.Scenario.str.extract(pattern, expand=False)
    df["Runtype"] = year.str[0]
    df["Year"] = year.str[1:]
    pattern = (
        r"([MCS][MDT][A-Za-z]*)"  # pattern that matches M, C or S and then M, D or T
    )
    df["Method"] = df.Scenario.str.extract(pattern, expand=False).fillna("ST")
    pattern = (
        r"(S\d+T\d+)"  # pattern that matches S and any number and T and any number
    )
    df["Resolution"] = df.Scenario.str.extract(pattern, expand=False).fillna("ST")

    # Pivot
    test = df.pivot_table(
        index=[
            "Scenario",
            "ShortSC",
            "Region",
            "Resolution",
            "Runtype",
            "Year",
            "Commodity",
        ],
        columns=["Method", "Parameter"],
        values="Value",
        aggfunc="sum",
    )
    final = df.pivot_table(
        index=["ShortSC", "Region", "Resolution", "Runtype", "Year", "Commodity"],
        columns=["Method", "Parameter"],
        values="Value",
        aggfunc="mean",
    )

    # Test if sum is the same, if not, final df actually did averaging across scenarios
    assert test.sum().sum() == final.sum().sum(), (
        f"ERROR: Some scenarios were summed!\nTest table (sum)\n{test}\n\nFinal table (mean)\n{final}"
    )

    return final


def format_backcap_adequacy_results(df: pd.DataFrame):
    # Get method, resolution, year and runtype
    pattern = (
        r"([FR]20[345]0)"  # pattern that matches R or F and then 2030, 2040 or 2050
    )
    df["ShortSC"] = df.Scenario.str.replace("_" + pattern, "", regex=True)
    year = df.Scenario.str.extract(pattern, expand=False)
    df["Runtype"] = year.str[0]
    df["Year"] = year.str[1:]
    pattern = (
        r"([MCS][MDT][A-Za-z]*)"  # pattern that matches M, C or S and then M, D or T
    )
    df["Method"] = df.Scenario.str.extract(pattern, expand=False).fillna("ST")
    pattern = (
        r"(S\d+T\d+)"  # pattern that matches S and any number and T and any number
    )
    df["Resolution"] = df.Scenario.str.extract(pattern, expand=False).fillna("ST")

    # Pivot
    test = df.pivot_table(
        index=[
            "ShortSC",
            "Scenario",
            "Region",
            "Resolution",
            "Runtype",
            "Year",
            "Commodity",
        ],
        columns=["Method"],
        values="Value",
        aggfunc="sum",
    )
    final = df.pivot_table(
        index=["ShortSC", "Region", "Resolution", "Runtype", "Year", "Commodity"],
        columns=["Method"],
        values="Value",
        aggfunc="mean",
    )

    # Test if sum is the same, if not, final df actually did averaging across scenarios
    assert test.sum().sum() == final.sum().sum(), (
        f"ERROR: Some scenarios were summed!\nTest table (sum)\n{test}\n\nFinal table (mean)\n{final}"
    )

    return final


def collect_adequacy_results(nth_max: int = 1):
    """Collect all adeq files in analysis/output"""

    path = Path("analysis/output")
    df_lole_ens = pd.DataFrame()
    df_backcap = pd.DataFrame()
    for p in path.iterdir():
        if "_adeq" in str(p) and p.name != "adeq_collected.csv":
            temp = pd.read_csv(p, index_col=0, header=[0, 1])
            if len(temp) > 0:
                temp = temp.stack().stack().reset_index()
                temp.columns = ["Region", "Commodity", "Parameter", "Value"]
                scenario = p.name.split("_adeq")[0]
                temp["Scenario"] = scenario
                df_lole_ens = pd.concat((df_lole_ens, temp))
        elif f"_backcapN{nth_max}.csv" in str(p) and p.name != "backcap_collected.csv":
            temp = pd.read_csv(p)
            if len(temp) > 0:
                scenario = p.name.split(f"_backcapN{nth_max}")[0]
                temp["Scenario"] = scenario
                temp = (
                    temp.pivot_table(index=["Scenario", "Region"]).stack().reset_index()
                )
                temp.columns = ["Scenario", "Region", "Commodity", "Value"]
                df_backcap = pd.concat((df_backcap, temp))

    df_lole_ens.to_csv("analysis/output/adeq_collected.csv", index=False)
    df_backcap.to_csv("analysis/output/backcap_collected.csv", index=False)


def backup_production(pro_ycragfst: pd.DataFrame, commodity: str = "ELECTRICITY") -> pd.DataFrame:
    """BACKUP-generation rows from PRO_YCRAGFST, filtered to one commodity.
    Balmorel only stores nonzero production in a GDX, so every row here is
    an hour backup was actually needed."""
    return pro_ycragfst.query('Generation.str.contains("BACKUP") and Commodity == @commodity')


def effective_backup_capacity(backup: pd.DataFrame, nth_max: int = 1) -> pd.DataFrame:
    """Per (Scenario, Year, Region): the nth-largest hourly backup
    production (nth_max=1 -> the maximum). A proxy for peaker "capacity",
    since Balmorel's own BACKUP nameplate capacity is set heuristically
    large purely to guarantee feasibility, not a real constraint (see
    ../../../../docs/adr/0005-peaker-effective-capacity-for-flex-option-plots.md
    in the GREAT repo this submodule is checked out in)."""
    return (
        backup.groupby(["Scenario", "Year", "Region"])["Value"]
        .apply(lambda x: x.nlargest(nth_max).iloc[-1])
        .reset_index()
    )


def compute_lole_ens(backup: pd.DataFrame) -> pd.DataFrame:
    """Per (Scenario, Year, Region): LOLE (h - count of hours backup was
    used) and ENS (TWh - summed backup production). Same definition as the
    `adequacy` CLI command, generalized to run in-memory across many
    scenarios/years at once instead of one scenario with CSV round-trips."""
    grouped = backup.groupby(["Scenario", "Year", "Region"])["Value"]
    return pd.DataFrame({"lole_h": grouped.count(), "ens_twh": grouped.sum() / 1e6}).reset_index()


# ------------------------------- #
#            2. Main              #
# ------------------------------- #


if __name__ == "__main__":
    collect_adequacy_results()
