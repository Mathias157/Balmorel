"""
Create exogenous electricity profiles based on Balmorel results

E.g. to test the impact of 'assuming' electricity demands of a sector
instead of endogenously modelling it.

Created on 29.05.2026
@author: Mathias Berg Rosendal
         PostDoc at DTU Management (Energy Economics & Modelling)
"""
# ------------------------------- #
#        0. Script Settings       #
# ------------------------------- #

# import matplotlib.pyplot as plt
# import pandas as pd
# import numpy as np
from pybalmorel import MainResults, IncFile
import click
from copy import copy

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


@click.pass_context
def simple_conversion(ctx, category: str, area_filter: str = ""):

    # Make .inc file with new DEUSER and the profile and annual demand
    exo_category = category.replace("ENDO", "EXO").replace("ENDOGENOUS", "EXO")

    profile = ctx.obj["profile"].query(f'Category == "{category}"')
    DE_VAR_T = copy(ctx.obj["DE_VAR_T"])
    DE_VAR_T.name += "_" + exo_category
    DE_VAR_T.body = profile
    DE_VAR_T.body["DEUSER"] = exo_category
    DE_VAR_T.body_prepare(["Region", "DEUSER"], columns=["Season", "Time"])
    DE_VAR_T.save()

    annual = ctx.obj["annual"].query(f'Category == "{category}"')
    DE = copy(ctx.obj["DE"])
    DE.name += "_" + exo_category
    DE.body = annual
    DE.body["DEUSER"] = exo_category
    DE.body_prepare(["Year", "Region"], columns="DEUSER")
    DE.save()


@click.pass_context
def power_to_heat(ctx, area_query: str, new_deuser_name: str):

    result = ctx.obj["result"]
    year = ctx.obj["profile"].Year.unique()[0]

    annual = result.get_result("F_CONS_YCRA").query(
        f"{area_query} and Technology == 'ELECT-TO-HEAT'"
    )
    annual.Value = annual.Value.round() * 1e6

    profile = result.get_result("F_CONS_YCRAST").query(
        f"{area_query} and Technology == 'ELECT-TO-HEAT' and Year == '{year}'"
    )

    DE_VAR_T = copy(ctx.obj["DE_VAR_T"])
    DE_VAR_T.name += "_" + new_deuser_name
    DE_VAR_T.body = profile
    DE_VAR_T.body["DEUSER"] = new_deuser_name
    DE_VAR_T.body_prepare(["Region", "DEUSER"], columns=["Season", "Time"])
    DE_VAR_T.save()

    DE = copy(ctx.obj["DE"])
    DE.name += "_" + new_deuser_name
    DE.body = annual
    DE.body["DEUSER"] = new_deuser_name
    DE.body_prepare(["Year", "Region"], columns="DEUSER")
    DE.save()


# ------------------------------- #
#            2. Main              #
# ------------------------------- #


@click.command()
@click.pass_context
@click.option(
    "--scenario",
    type=str,
    default="APS_base_allflex_INV",
    help="Scenario name, assumed as suffix on MainResults_*.gdx",
)
@click.option("--year", type=str, default=2050, help="Model year to use profiles from")
@click.option(
    "--mainresults-path",
    type=str,
    default="base/model",
    help="Path to MainResults file",
)
@click.option(
    "--gams-system-directory",
    type=str,
    default="/opt/gams/53",
    help="Path to GAMS system directory",
)
def main(ctx, scenario, year, mainresults_path, gams_system_directory):

    result = MainResults(
        f"MainResults_{scenario}.gdx",
        mainresults_path,
        system_directory=gams_system_directory,
    )

    profile = result.get_result("EL_DEMAND_YCRST").query(f"Year == '{year}'")
    annual = result.get_result("EL_DEMAND_YCR")
    annual.Value = annual.Value.round() * 1e6

    DE_VAR_T = IncFile(
        name="DE_VAR_T",
        path=".",
        prefix='%onmulti%\nPARAMETER DE_VAR_T(RRR,DEUSER,SSS,TTT) "Variation in electricity demand"\n',
        suffix="\n;\n%offmulti%",
    )
    DE = IncFile(
        name="DE",
        path=".",
        prefix='%onmulti%\nPARAMETER DE(YYY,RRR,DEUSER) "Annual electricity consumption (MWh)"\n',
        suffix="\n;\n%offmulti%",
    )

    ctx.ensure_object(dict)
    ctx.obj["result"] = result
    ctx.obj["profile"] = profile
    ctx.obj["annual"] = annual
    ctx.obj["DE_VAR_T"] = DE_VAR_T
    ctx.obj["DE"] = DE

    simple_conversion("ENDO_H2")
    simple_conversion("ENDO_EV")

    # Industry power-to-heat electricity profile
    power_to_heat("Area.str.contains('IND')", "IND")
    # Individual power-to-heat electricity profile
    power_to_heat("Area.str.contains('IDVU')", "IDVU")
    # District heating power-to-heat electricity profile
    power_to_heat(
        "not Area.str.contains('IDVU') and not Area.str.contains('IND')", "DH"
    )


if __name__ == "__main__":
    main()
