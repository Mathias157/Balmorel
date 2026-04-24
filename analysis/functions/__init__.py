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

def collect_adequacy_results():
    """Collect all adeq files in analysis/output"""

    path=Path('analysis/output')
    df=pd.DataFrame()
    for p in path.iterdir():
        if '_adeq' in str(p) and p.name != 'adeq_collected.csv':
            temp=pd.read_csv(p, index_col=0, header=[0,1])
            if len(temp) > 0:
                temp=temp.stack().stack().reset_index()
                temp.columns = ['Region', 'Commodity', 'Parameter', 'Value']
                scenario=p.name.split('_adeq')[0]
                temp['Scenario'] = scenario
                df=pd.concat((df, temp))

    # df.columns.names = ['Value', 'Commodity']
    df.to_csv('analysis/output/adeq_collected.csv', index=False)

# ------------------------------- #
#            2. Main              #
# ------------------------------- #


if __name__ == '__main__':
    collect_adequacy_results()

