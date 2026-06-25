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
from zoneinfo import ZoneInfo
from pathlib import Path
import click
from decouple import config
from pybalmorel import MainResults
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
    "DE4-E": "DE",
    "DE4-N": "DE",
    "DE4-S": "DE",
    "DE4-W": "DE",
    "FIN": "FI",
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


def load_entsoe_data(year: int, resampling: str = "h"):
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

            # Get time and resample to hours
            temp.Time = pd.to_datetime(temp.Time, utc=True).dt.tz_convert(
                "Europe/Copenhagen",
            )
            temp = (
                temp.resample(
                    resampling,
                    on="Time",
                )
                .aggregate({"Value": "mean"})
                .reset_index()
            )

            region = format_entsoe_region_name(item, year, "load")
            temp["Region"] = region

            loads = pd.concat((loads, temp), ignore_index=True)
        elif item.match("*_day_ahead_prices.csv"):
            temp = pd.read_csv(item).rename(
                columns={"Unnamed: 0": "Time", "0": "Value"}
            )
            region = format_entsoe_region_name(item, year, "day_ahead_prices")
            temp["Region"] = region

            # Get time
            temp.Time = pd.to_datetime(temp.Time, utc=True).dt.tz_convert(
                "Europe/Copenhagen",
            )

            elprices = pd.concat((elprices, temp), ignore_index=True)

        else:
            warn(f"{item} was not loaded as it did not match naming pattern.", Warning)
            continue

    return loads, elprices


def format_balmorel_df(df: pd.DataFrame, year: int):
    if not (df.Season.unique().shape[0] == 52 and df.Time.unique().shape[0] == 168):
        raise ValueError("Temporal structure not recognised!")

    new_timeindex = (
        pd.date_range(
            f"{year}-01-01 00:00",
            f"{year}-12-31 23:00",
            freq="h",
            tz=ZoneInfo("Europe/Copenhagen"),
        )
        .isocalendar()
        .reset_index()
    )

    # Get index of first monday and last sunday
    first_monday_hour = new_timeindex.iloc[:168, :].query("day == 1").index[0]
    last_sunday_hour = new_timeindex.query("day == 7").index[-1]
    new_timeindex = new_timeindex.loc[first_monday_hour:last_sunday_hour, "index"]

    # Insert to Balmorel df
    df_out = df.pivot_table(
        index=["Season", "Time"], columns="Region", values="Value", aggfunc="sum"
    )
    df_out.index = new_timeindex
    df_out = df_out.stack().reset_index()
    df_out.columns = ["Time", "Region", "Value"]

    return df_out


def load_balmorel_data(
    scenario_name: str, scenario_folder_path: str, year: int, overwrite: bool
):
    "Load df from MainResults"

    path = Path("analysis/output")
    if (
        not path.joinpath("balmorel_prices.csv").exists()
        or not path.joinpath("balmorel_load.csv").exists()
    ) or overwrite:
        results = MainResults(
            f"MainResults_{scenario_name}.gdx",
            paths=Path(scenario_folder_path).absolute().__str__(),
            system_directory=config("GAMS_SYSTEM_DIR", None),
        )  # pyright: ignore
        load = results.get_result("EL_DEMAND_YCRST").query(f"Year == '{year}'")
        elprices = results.get_result("EL_PRICE_YCRST").query(f"Year == '{year}'")
        load.to_csv(path.joinpath("balmorel_load.csv"), index=False)
        elprices.to_csv(path.joinpath("balmorel_prices.csv"), index=False)
    else:
        load = pd.read_csv(path.joinpath("balmorel_load.csv"))
        elprices = pd.read_csv(path.joinpath("balmorel_prices.csv"))

    return load, elprices


def calculate_statistics(df):
    "Get std. dev, mean, max etc..."
    pass


def aggregate_regions(df: pd.DataFrame, aggfunc: str, time_columns: list):
    "Aggregate DE4, IT-* etc"

    for region in df.Region.unique():
        if region in bidding_zone_translation:
            df = (
                df.replace({"Region": {region: bidding_zone_translation[region]}})
                .pivot_table(
                    index=["Region"] + time_columns,
                    values="Value",
                    aggfunc=aggfunc,
                )
                .reset_index()
            )
            print(f"Aggregating {region} to {bidding_zone_translation[region]}")

    return df


def load_and_align_regions(
    balmorel_scenario: str,
    balmorel_scenario_path: str,
    year: int,
    elpriceaggfunc: str,
    overwrite: bool,
):
    entsoe_load, entsoe_elprices = load_entsoe_data(year)
    entsoe_load = aggregate_regions(entsoe_load, "sum", ["Time"])
    entsoe_elprices = aggregate_regions(entsoe_elprices, elpriceaggfunc, ["Time"])
    entsoe_load_unique_regions = set(entsoe_load.Region.unique())
    entsoe_elprices_unique_regions = set(entsoe_elprices.Region.unique())
    print(f"Amount of regions in ENTSO-E Load data: {entsoe_load_unique_regions}")
    print(
        f"Amount of regions in ENTSO-E El. prices data: {entsoe_elprices_unique_regions}"
    )
    set_difference = entsoe_load_unique_regions.difference(
        entsoe_elprices_unique_regions
    )
    if set_difference:
        print(f"Difference in region sets: {set_difference}")
    else:
        print("No regional differences between ENTSO-E load and el. price results")
    balmorel_load, balmorel_elprices = load_balmorel_data(
        balmorel_scenario, balmorel_scenario_path, year, overwrite
    )
    balmorel_load = format_balmorel_df(
        aggregate_regions(balmorel_load, "sum", ["Season", "Time"]), year
    )
    balmorel_elprices = format_balmorel_df(
        aggregate_regions(balmorel_elprices, elpriceaggfunc, ["Season", "Time"]),
        year,
    )
    balmorel_load_unique_regions = set(balmorel_load.Region.unique())
    balmorel_elprices_unique_regions = set(balmorel_elprices.Region.unique())
    print(f"Amount of regions in Balmorel Load data: {balmorel_load_unique_regions}")
    print(
        f"Amount of regions in Balmorel El. prices data: {balmorel_elprices_unique_regions}"
    )
    set_difference = balmorel_load_unique_regions.difference(
        balmorel_elprices_unique_regions
    )
    if set_difference:
        print(f"Difference in region sets: {set_difference}")
    else:
        print("No regional differences between Balmorel load and el. price results")

    entsoe_unique_regions = entsoe_load_unique_regions.intersection(
        entsoe_elprices_unique_regions
    )
    balmorel_unique_regions = balmorel_load_unique_regions.intersection(
        balmorel_elprices_unique_regions
    )
    dataset_difference = entsoe_unique_regions.difference(balmorel_unique_regions)
    if dataset_difference:
        print(
            f"Regional differnces in dataset and Balmorel scope: {dataset_difference}"
        )

    # Join datasets
    prices = (
        entsoe_elprices.set_index(["Region", "Time"])
        .rename(columns={"Value": "ENTSOE"})
        .join(
            (
                balmorel_elprices.rename(columns={"Value": "BALMOREL"}).set_index(
                    ["Region", "Time"]
                )
            ),
            how="inner",
        )
    )

    loads = (
        entsoe_load.set_index(["Region", "Time"])
        .rename(columns={"Value": "ENTSOE"})
        .join(
            balmorel_load.rename(columns={"Value": "BALMOREL"}).set_index(
                ["Region", "Time"]
            ),
            how="inner",
        )
    )

    return prices, loads


# ------------------------------- #
#            2. Main              #
# ------------------------------- #


@click.argument("balmorel-scenario", type=str, default="backcast_R2024")
@click.argument("balmorel-scenario-path", type=str, default="backcast/model")
@click.argument("year", type=int, default=2024)
@click.argument("elpriceaggfunc", type=str, default="mean")
@click.option("--overwrite", "-o", is_flag=True, default=False)
@click.command()
def main(balmorel_scenario, balmorel_scenario_path, year, elpriceaggfunc, overwrite):
    prices, loads = load_and_align_regions(
        balmorel_scenario, balmorel_scenario_path, year, elpriceaggfunc, overwrite
    )
    calculate_statistics(prices)
    calculate_statistics(loads)


if __name__ == "__main__":
    main()
