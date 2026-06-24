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
from warnings import warn

# Replace with pybalmorel.entsoe import in the future
# import sys
# sys.path.append("/home/mberos/Repos/pybalmorel/src/pybalmorel")
# print(sys.path)
# from entsoe import bidding_zone_codes, bidding_zones
reversed_bidding_zone_codes = {
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

bidding_zone_codes = {
    "10Y1001A1001A73I": "IT-NORD",
    "10Y1001A1001A70O": "IT-CNOR",
    "10Y1001A1001A71M": "IT-CSUD",
    "10Y1001A1001A788": "IT-SUD",
    "10Y1001C--00096J": "IT-Calabria",
    "10Y1001A1001A75E": "IT-Sicily",
    "10Y1001A1001A74G": "IT-Sardinia",
    "10YNO-1--------2": "NO1",
    "10YNO-2--------T": "NO2",
    "10YNO-3--------J": "NO3",
    "10YNO-4--------9": "NO4",
    "10Y1001A1001A48H": "NO5",
    "10Y1001A1001A44P": "SE1",
    "10Y1001A1001A45N": "SE2",
    "10Y1001A1001A46L": "SE3",
    "10Y1001A1001A47J": "SE4",
    "10YBA-JPCC-----D": "BA",
    "10YDK-1--------W": "DK1",
    "10YDK-2--------M": "DK2",
    "IE_SEM": "IE",
    "DE_LU": "DE",
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

balmorel_regions = [
    "DK1",
    "DK2",
    "NO1",
    "NO2",
    "NO3",
    "NO4",
    "NO5",
    "FIN",
    "DE4-E",
    "DE4-N",
    "DE4-S",
    "DE4-W",
    "NL",
    "SE1",
    "SE2",
    "SE3",
    "SE4",
    "UK",
    "EE",
    "LV",
    "LT",
    "PL",
    "BE",
    "FR",
    "IT",
    "CH",
    "AT",
    "CZ",
    "ES",
    "PT",
    "SK",
    "HU",
    "SI",
    "HR",
    "RO",
    "BG",
    "GR",
    "IE",
    "LU",
    "AL",
    "ME",
    "MK",
    "BA",
    "RS",
    "MT",
    "CY",
]

bidding_zone_translation = {
    "IT-NORD": "IT",
    "IT-CNOR": "IT",
    "IT-CSUD": "IT",
    "IT-SUD": "IT",
    "IT-Calabria": "IT",
    "IT-Sicily": "IT",
    "IT-Sardinia": "IT",
}

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


def format_entsoe_region_name(path, year, parameter):
    raw_region_name = path.name.lstrip(f"{year}_").rstrip(f"_{parameter}.csv")
    if raw_region_name in bidding_zone_codes:
        region = bidding_zone_codes[raw_region_name]
    else:
        region = raw_region_name
    return region


def load_entsoe_data(year):
    "Load csvs"
    path = Path("backcast/entsoedata")

    loads = pd.DataFrame()
    elprices = pd.DataFrame()
    for item in path.iterdir():
        # Load data for a specific region
        if item.match("*_load.csv"):
            temp = pd.read_csv(item).rename(
                columns={"Unnamed: 0": "Time", "Actual Load": "Value"}
            )
            region = format_entsoe_region_name(item, year, "load")
            temp["Region"] = region
            loads = pd.concat((loads, temp))
        elif item.match("*_day_ahead_prices.csv"):
            temp = pd.read_csv(item).rename(
                columns={"Unnamed: 0": "Time", "0": "Value"}
            )
            region = format_entsoe_region_name(item, year, "day_ahead_prices")
            temp["Region"] = region
            elprices = pd.concat((elprices, temp))
        else:
            warn(f"{item} was not loaded as it did not match naming pattern.", Warning)
            continue

    return loads, elprices


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
    entsoe_load, entsoe_elprices = load_entsoe_data(2024)
    print(f"Amount of regions in ENTSO-E Load data: {len(entsoe_load.Region.unique())}")
    print(
        f"Amount of regions in ENTSO-E El. prices data: {len(entsoe_elprices.Region.unique())}"
    )
    balmorel_load, balmorel_elprices = load_balmorel_data()
    print(
        f"Amount of regions in Balmorel Load data: {len(balmorel_load.Region.unique())}"
    )
    print(
        f"Amount of regions in Balmorel El. prices data: {len(balmorel_elprices.Region.unique())}"
    )


if __name__ == "__main__":
    main()
