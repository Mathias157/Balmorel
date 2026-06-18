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

import numpy as np
from pybalmorel import MainResults, IncFile
import click
from copy import copy

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #


@click.pass_context
def simple_conversion(ctx, category: str):

    # Make .inc file with new DEUSER and the profile and annual demand
    exo_category = category.replace("ENDO", "EXO").replace("ENDOGENOUS", "EXO")

    profile = ctx.obj["profile"].query(f'Category == "{category}" and Value > 0')

    DE_VAR_T = copy(ctx.obj["DE_VAR_T"])
    DE_VAR_T.name += "_" + exo_category
    DE_VAR_T.prefix = DE_VAR_T.prefix.replace("DE_VAR_T", "DE_VAR_T_" + exo_category)
    DE_VAR_T.suffix = f"\n;\nDE_VAR_T(RRR,'{exo_category}',SSS,TTT) = DE_VAR_T_{exo_category}(RRR,'{exo_category}',SSS,TTT);\nDE_VAR_T_{exo_category}(RRR,'{exo_category}',SSS,TTT)=0;"
    DE_VAR_T.body = profile
    DE_VAR_T.body["DEUSER"] = exo_category
    DE_VAR_T.body_prepare(["Region", "DEUSER"], columns=["Season", "Time"])
    DE_VAR_T.save()

    # Get negative demand (V2G for EVs)
    negative_sum = (
        ctx.obj["all_profiles"]
        .query(f'Value < 0 and Category == "{category}"')
        .pivot_table(index="Year", columns="Region", values="Value", aggfunc="sum")
    )
    positive_sum = (
        ctx.obj["all_profiles"]
        .query(f'Value > 0 and Category == "{category}"')
        .pivot_table(index="Year", columns="Region", values="Value", aggfunc="sum")
    )
    negative_fraction_of_positive = (positive_sum + negative_sum) / positive_sum

    annual = ctx.obj["annual"].query(f'Category == "{category}"')

    DE = copy(ctx.obj["DE"])
    DE.name += "_" + exo_category
    DE.prefix = DE.prefix.replace("DE(", "DE_" + exo_category + "(").replace(
        f"DE_{exo_category}USER", "DEUSER"
    )
    DE.suffix = f"\n;\nDE(YYY, RRR,'{exo_category}') = DE_{exo_category}(YYY, RRR,'{exo_category}');\nDE_{exo_category}(YYY, RRR,'{exo_category}')=0;"
    DE.body = annual
    DE.body["DEUSER"] = exo_category
    DE.body_prepare(["Year", "Region"], columns="DEUSER")

    if negative_sum.sum().sum() < -1e-4:
        DE.suffix += "\n\n* Reducing demand by share of negative demand"
        # Reduce annual demand by the percentage reduction of the positive sum when accounting for negative sum
        for year, row in negative_fraction_of_positive.iterrows():
            for region in row.index:
                if not np.isnan(row[region]) and row[region] != 1:
                    DE.suffix += f"\nDE('{year}','{region}','{exo_category}')=DE('{year}','{region}','{exo_category}')*{row[region]};"

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
    DE_VAR_T.prefix = DE_VAR_T.prefix.replace("DE_VAR_T", "DE_VAR_T_" + new_deuser_name)
    DE_VAR_T.suffix = f"\n;\nDE_VAR_T(RRR,'{new_deuser_name}',SSS,TTT) = DE_VAR_T_{new_deuser_name}(RRR,'{new_deuser_name}',SSS,TTT);\nDE_VAR_T_{new_deuser_name}(RRR,'{new_deuser_name}',SSS,TTT)=0;"
    DE_VAR_T.body = profile
    DE_VAR_T.body["DEUSER"] = new_deuser_name
    DE_VAR_T.body_prepare(["Region", "DEUSER"], columns=["Season", "Time"])
    DE_VAR_T.save()

    DE = copy(ctx.obj["DE"])
    DE.name += "_" + new_deuser_name
    DE.prefix = DE.prefix.replace("DE", "DE_" + new_deuser_name).replace(
        f"DE_{new_deuser_name}USER", "DEUSER"
    )
    DE.suffix = f"\n;\nDE(YYY, RRR,'{new_deuser_name}') = DE_{new_deuser_name}(YYY, RRR,'{new_deuser_name}');\nDE_{new_deuser_name}(YYY, RRR,'{new_deuser_name}')=0;"
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

    profile = result.get_result("EL_DEMAND_YCRST")
    annual = result.get_result("EL_DEMAND_YCR")
    annual.Value = annual.Value.round() * 1e6

    DE_VAR_T = IncFile(
        name="DE_VAR_T",
        path=".",
        prefix='\nTABLE DE_VAR_T(RRR,DEUSER,SSS,TTT) "Variation in electricity demand"\n',
    )
    DE = IncFile(
        name="DE",
        path=".",
        prefix='\nTABLE DE(YYY,RRR,DEUSER) "Annual electricity consumption (MWh)"\n',
    )

    ctx.ensure_object(dict)
    ctx.obj["result"] = result
    ctx.obj["profile"] = profile.query(f"Year == '{year}'")
    ctx.obj["all_profiles"] = profile
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
