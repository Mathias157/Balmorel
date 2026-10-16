"""
Verifications of the model

Commands that verify that the model is not behaving nonsensical

Created on 19.03.2026
@author: Mathias Berg Rosendal
         PhD Student at DTU Management (Energy Economics & Modelling)
"""
# ------------------------------- #
#        0. Script Settings       #
# ------------------------------- #

from pathlib import Path
from pybalmorel.utils import symbol_to_df
from gams import GamsWorkspace
from functions import find_result
import click
import warnings
import pandas as pd

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #



# ------------------------------- #
#            2. Main              #
# ------------------------------- #

@click.group()
@click.pass_context
@click.argument('sc-folder', type=str)
def main(ctx, sc_folder):
    """
    CLI for verifications
    """
    
    ctx.ensure_object(dict)
    ctx.obj['sc-folder'] = sc_folder
    

@main.command()
@click.pass_context
def check_all(ctx):
    """
    Run all verifications
    """
    
    ctx.invoke(debug_vars, sc_folder=ctx.obj['sc-folder'])


@main.command()
@click.pass_context
def debug_vars(ctx):
    """
    Check that the debug variables are not crazy
    """

    sc_folder = ctx.obj["sc-folder"]
    ws=GamsWorkspace()
    db=ws.add_database_from_gdx(str(Path(f'{sc_folder}/model/all_endofmodel.gdx').absolute()))

    for var in ['VQHEQ', 'VQHYRSMINVOL', 'VQHYRSSEQ']:
        df=symbol_to_df(db, var)
        if len(df.columns) != 0:
            stats = df.Value.min(), df.Value.mean(), df.Value.max()
            if stats[2] > 1:
                warnings.warn(f"{var} DEBUG VARIABLE ABOVE 1!")
            print(f"{var} debug variable statistics:")
            print(f"Min: {stats[0]}")
            print(f"Mean: {stats[1]}")
            print(f"Max: {stats[2]}")
        else:
            print(f"{var} debug variable not used")

@main.command()
@click.pass_context
@click.option('--scenario', type=str, default='', help="Check a specific MainResults file in the folder")
def ev_results(ctx, scenario):
    """
    Check EV results
    """
    
    # Get MainResults file
    sc_folder=ctx.obj['sc-folder']
    res = find_result(sc_folder, scenario)

    # Load results 
    df = (
        res
        .get_result('EL_DEMAND_YCRST')
        .query('Category == "ENDO_EV"')
    )

    # Check max, mean and min
    df_max = (
        df
        .pivot_table(index=['Year', 'Region'],
                    values='Value',
                    aggfunc='max')
        .rename(columns={'Value' : 'Max'})
    )
    df_mean = (
        df
        .pivot_table(index=['Year', 'Region'],
                    values='Value',
                    aggfunc='mean')
        .rename(columns={'Value' : 'Mean'})
    )
    df_min = (
        df
        .pivot_table(index=['Year', 'Region'],
                    values='Value',
                    aggfunc='min')
        .rename(columns={'Value' : 'Min'})
    )
    df_max_pct = df_max['Max'] / df_mean['Mean'] * 100
    df_min_pct = df_min['Min'] / df_mean['Mean'] * 100
    df = (
        df_max
        .join(df_mean)
        .join(df_min)
    )
    df['Max % of Mean'] = df_max_pct
    df['Min % of Mean'] = df_min_pct
    print(df.round())


@main.command()
@click.pass_context
@click.option('--scenario', type=str, default='', help="Check a specific MainResults file in the folder")
@click.option('--generations', type=str, default=r'.*NUCL_CND_E-33(?:_Y-20(?:25|35))?$', show_default=True,
              help="Regex for the unit-commitment generation names to check (only those with an active ramp equation, i.e. GDUCRAMP*CHRONOHOUR < 1)")
@click.option('--ramp-rate', type=float, default=0.125, show_default=True, help="GDUCRAMPU/D of the checked generations (share of capacity per hour)")
@click.option('--chronohour', type=float, default=6, show_default=True, help="Hours per time step (CHRONOHOUR)")
@click.option('--swing', type=float, default=0.6, show_default=True,
              help="1 - GDUCGMIN: largest step change possible without (de)committing units")
def ramp_bound(ctx, scenario, generations, ramp_rate, chronohour, swing):
    """
    Check unit-commitment ramping against the LP/RMIP fleet ramp rate

    The fleet ramp rate bound (ADR 0003 in Balmorel) is
    |dPRO| <= ramp-rate * chronohour * available capacity per time step.
    MainResults has no available capacity or UC variables, so it is
    approximated in two ways:
    - VIOLATION: step change above the bound on installed capacity, which
      the bound can never allow (available <= installed). Results from before
      Balmorel ADR 0004 counted existing units as CEIL(GKFX/GDUCUNITSIZE), so
      output could exceed installed capacity there
    - SUSPECT: step change above the bound on the largest output of that
      generation in the year (a lower estimate of available capacity)
    The swing column flags step changes larger than full load to minimum
    load, i.e. ones that needed units to start or shut down within the step.
    """

    sc_folder = ctx.obj['sc-folder']
    res = find_result(sc_folder, scenario)

    pro = (
        res
        .get_result('PRO_YCRAGFST')
        .query('Commodity == "ELECTRICITY" and Generation.str.match(@generations)', engine='python')
    )
    if pro.empty:
        print(f"No production for generations matching '{generations}'")
        return
    cap = (
        res
        .get_result('G_CAP_YCRAF')
        .query('Commodity == "ELECTRICITY" and Generation.str.match(@generations)', engine='python')
        .groupby(['Year', 'Area', 'Generation'])
        .Value.sum()
        .mul(1e3)  # GW -> MW, PRO_YCRAGFST is MW per time step
        .rename('Capacity')
    )

    # Production on the full S,T grid (missing = 0), in chronological order
    pro = pro.pivot_table(index=['Year', 'Area', 'Generation'],
                          columns=['Season', 'Time'],
                          values='Value',
                          aggfunc='sum',
                          fill_value=0)
    pro = pro.reindex(sorted(pro.columns), axis=1, fill_value=0)
    # Within-season steps only: with SEASONALLINKUC off (GREAT's full-year
    # and rolling runs) there is no ramp equation across season boundaries
    step = pro.T.groupby(level='Season').diff().T.dropna(axis=1, how='all')

    df = pd.DataFrame({
        'Capacity': cap,
        'MaxOutput': pro.max(axis=1),
        'MaxUp': step.max(axis=1),
        'MaxDown': -step.min(axis=1),
    }).dropna(subset=['MaxUp'])
    df = df[df.Capacity > 0]
    bound = ramp_rate * chronohour
    df['MaxRamp/Cap'] = df[['MaxUp', 'MaxDown']].max(axis=1) / df.Capacity
    df['MaxRamp/MaxOutput'] = df[['MaxUp', 'MaxDown']].max(axis=1) / df.MaxOutput
    df['Violation'] = df['MaxRamp/Cap'] > bound * (1 + 1e-4)
    df['Suspect'] = df['MaxRamp/MaxOutput'] > bound * (1 + 1e-4)
    df['Swing'] = df['MaxRamp/Cap'] > swing * (1 + 1e-4)

    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 250):
        print(f"Bound: {bound:.3f} of available capacity per step ({ramp_rate}/h x {chronohour} h)\n")
        print(df.sort_values('MaxRamp/Cap', ascending=False).round(3))
    print(f"\n{df.Violation.sum()} violations, {df.Suspect.sum()} suspects, "
          f"{df.Swing.sum()} with (de)commitment within a step, out of {len(df)} area-generations")
    if df.Violation.any():
        warnings.warn("RAMP BOUND VIOLATED ON INSTALLED CAPACITY!")


if __name__ == '__main__':
    main()
