"""
Validation through Backcasting

Download data from ENTSO-E and compare to Balmorel simulation of similar year

Created on 24.06.2026
@author: Mathias Berg Rosendal
         PostDoc at DTU Management (Energy Economics & Modelling)
"""
# ------------------------------- #
#        0. Script Settings       #
# ------------------------------- #

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import click
from decouple import config
from pybalmorel import Balmorel

# Replace with pybalmorel.entsoe import in the future
# import sys
# sys.path.append("/home/mberos/Repos/pybalmorel/src/pybalmorel")
# print(sys.path)
# from entsoe import bidding_zone_codes, bidding_zones
bidding_zone_codes = {
    "IT-NORD": "10Y1001A1001A73I",
    "IT-CNOR": "10Y1001A1001A70O",
    "IT-CSUD": "10Y1001A1001A71M",
    "IT-SUD": "10Y1001A1001A788",
    "IT-Calabria": "10Y1001C--00096J",
    "IT-Sicily": "10Y1001A1001A75E",
    "IT-Sardinia": "10Y1001A1001A74G",
    "NO1": "10YNO-1--------2",
    "NO2": "10YNO-2--------T",
    "NO3": "10YNO-3--------J",
    "NO4": "10YNO-4--------9",
    "NO5": "10Y1001A1001A48H",
    "SE1": "10Y1001A1001A44P",
    "SE2": "10Y1001A1001A45N",
    "SE3": "10Y1001A1001A46L",
    "SE4": "10Y1001A1001A47J",
    "BA": "10YBA-JPCC-----D",
}

bidding_zones = [
    "IE_SEM",
    "10YGB----------A",
    "PT",
    "ES",
    "FR",
    "BE",
    "NL",
    "DE_LU",
    "10YDK-1--------W",
    "10YDK-2--------M",
    "10YNO-1--------2",
    "10YNO-2--------T",
    "10YNO-3--------J",
    "10YNO-4--------9",
    "10Y1001A1001A48H",
    "10Y1001A1001A47J",
    "10Y1001A1001A45N",
    "10Y1001A1001A46L",
    "10Y1001A1001A47J",
    "FI",
    "EE",
    "LV",
    "LT",
    "PL",
    "CZ",
    "SK",
    "HU",
    "RO",
    "BG",
    "GR",
    "AL",
    "MK",
    "XK",
    "ME",
    "RS",
    "10YBA-JPCC-----D",
    "HR",
    "SI",
    "AT",
    "CH",
    "10Y1001A1001A73I",
    "10Y1001A1001A70O",
    "10Y1001A1001A71M",
    "10Y1001A1001A788",
    "10Y1001C--00096J",
    "10Y1001A1001A75E",
    "10Y1001A1001A74G",
]


# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


def load_entsoe_data():
    "Load csvs"
    pass


def load_balmorel_data():
    "Load df from MainResults"

    path = Path("analysis/output")
    if (
        not path.joinpath("balmorel_prices.csv").exists()
        or not path.joinpath("balmorel_load.csv").exists()
    ):
        model = Balmorel(".", gams_system_directory=config("GAMS_SYSTEM_DIR"))  # pyright: ignore
        model.collect_results()
        load = model.results.get_result("EL_DEMAND_YCRST")
        elprices = model.results.get_result("EL_PRICE_YCRST")
        load.to_csv(path.joinpath("balmorel_load.csv"), index=False)
        elprices.to_csv(path.joinpath("balmorel_prices.csv"), index=False)
    else:
        load = pd.read_csv(path.joinpath("balmorel_load.csv"))
        elprices = pd.read_csv(path.joinpath("balmorel_prices.csv"))

    return load, elprices


def calculate_statistics(df):
    "Get std. dev, mean, max etc..."
    pass


def aggregate_entsoe_regions(df):
    "Aggregate IT etc"
    pass


def aggregate_balmorel_regions(df):
    "Aggregate DE4 etc"
    pass


# ------------------------------- #
#            2. Main              #
# ------------------------------- #


@click.command()
def main():
    df = load_balmorel_data()
    print(df[0].Region.unique())


if __name__ == "__main__":
    main()
