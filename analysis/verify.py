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
import gams.transfer as gt
from functions import find_result
import click
import warnings
import pandas as pd
import os

# ------------------------------- #
#          1. Functions           #
# ------------------------------- #

GAMS_SYSTEM_DIR=os.getenv('GAMS_SYSTEM_DIR')

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
    ws=GamsWorkspace(system_directory=GAMS_SYSTEM_DIR)
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
    res = find_result(sc_folder, scenario, GAMS_SYSTEM_DIR)

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
    res = find_result(sc_folder, scenario, GAMS_SYSTEM_DIR)

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


@main.command()
@click.pass_context
@click.option('--scenario', type=str, default='', help="Check a specific MainResults file in the folder")
@click.option('--gdata-gdx', type=str, default='',
              help="GDX with GDATA, used to limit the check to unit-commitment technologies (GDUC = 1) [default: <sc-folder>/model/all_endofmodel.gdx if it exists, otherwise all generations are checked]")
@click.option('--tolerance', type=float, default=0.01, show_default=True, help="Relative tolerance above installed capacity")
@click.option('--top', type=int, default=20, show_default=True, help="Number of worst area-generations to print")
def capacity_bound(ctx, scenario, gdata_gdx, tolerance, top):
    """
    Check that electricity output never exceeds installed capacity

    Before Balmorel ADR 0004, existing unit-commitment units were counted as
    CEIL(GKFX/GDUCUNITSIZE) under LP/RMIP, so output could reach the next
    whole unit above installed capacity. Compares the largest electricity
    output of each area-generation (PRO_YCRAGFST, MW per time step) with its
    installed capacity (G_CAP_YCRAF).
    """

    sc_folder = ctx.obj['sc-folder']
    res = find_result(sc_folder, scenario, GAMS_SYSTEM_DIR)

    # Unit-commitment technologies and their unit size, if GDATA is available
    gdata_gdx = Path(gdata_gdx or f'{sc_folder}/model/all_endofmodel.gdx')
    unit_size = None
    if gdata_gdx.exists():
        ws = GamsWorkspace(system_directory=GAMS_SYSTEM_DIR)
        db = ws.add_database_from_gdx(str(gdata_gdx.absolute()))
        gdata = {(rec.keys[0], rec.keys[1]): rec.value for rec in db['GDATA']}
        unit_size = pd.Series({g: gdata.get((g, 'GDUCUNITSIZE'), 0) for (g, p), v in gdata.items()
                               if p == 'GDUC' and v == 1}, name='UnitSize')
        print(f"Checking {len(unit_size)} unit-commitment technologies from {gdata_gdx}")
    else:
        print(f"{gdata_gdx} not found - checking all generations")

    cap = (
        res
        .get_result('G_CAP_YCRAF')
        .query('Commodity == "ELECTRICITY"')
        .groupby(['Year', 'Area', 'Generation'])
        .Value.sum()
        .mul(1e3)  # GW -> MW, PRO_YCRAGFST is MW per time step
        .rename('Capacity')
    )
    pro = (
        res
        .get_result('PRO_YCRAGFST')
        .query('Commodity == "ELECTRICITY"')
        .groupby(['Year', 'Area', 'Generation'])
        .Value.max()
        .rename('MaxOutput')
    )
    df = pd.concat([cap, pro], axis=1, join='inner')
    df = df[df.Capacity > 0]
    if unit_size is not None:
        df = df[df.index.get_level_values('Generation').isin(unit_size.index)]
        df['UnitSize'] = df.index.get_level_values('Generation').map(unit_size)
    df['Excess'] = df.MaxOutput - df.Capacity
    df['MaxOutput/Cap'] = df.MaxOutput / df.Capacity
    over = df[df['MaxOutput/Cap'] > 1 + tolerance]

    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 250):
        print(over.sort_values('Excess', ascending=False).head(top).round(2))
    print(f"\n{len(over)} of {len(df)} area-generations above installed capacity, "
          f"{over.Excess.sum() / 1e3:.1f} GW in total at their maximum output")
    if len(over):
        warnings.warn("ELECTRICITY OUTPUT ABOVE INSTALLED CAPACITY!")


@main.command()
@click.pass_context
@click.option('--scenario', type=str, default='', help="Check a specific MainResults file in the folder")
@click.option('--threshold', type=float, default=1e4, show_default=True,
              help="Price (money/MWh) above which an hour counts as penalty-set - backup generators cost at most 3000")
def penalty_prices(ctx, scenario, threshold):
    """
    Check that no commodity price is set by an infeasibility penalty

    Every VQ*/slack variable enters QOBJ at PENALTYQ (1e9), so when one binds,
    the duals - and every price derived from them - jump to 1e5-1e7 money/MWh,
    while volumes can still look normal. Counts such hours per price symbol and
    lists the seasons they occur in. See docs/adr/0047-backup-heat-in-every-heat-demand-area.md.
    """

    sc_folder = ctx.obj['sc-folder']
    res = find_result(sc_folder, scenario, GAMS_SYSTEM_DIR)
    gdx = str(Path(res.paths[0], res.files[0]).absolute())
    print(f"Checking {gdx}")

    # Read only the price symbols - rolling MainResults are several GB
    symbols = ['EL_PRICE_YCRST', 'H_PRICE_YCRAST', 'H2_PRICE_YCRST', 'BIOMETH_PRICE_YST']
    container = gt.Container(system_directory=GAMS_SYSTEM_DIR)
    container.read(gdx, records=False)
    present = [symbol for symbol in symbols if symbol in container]
    container = gt.Container(system_directory=GAMS_SYSTEM_DIR)
    container.read(gdx, symbols=present + ['H_DEMAND_YCRA'])

    # Areas without heat demand are empty heat nodes whose price is an arbitrary dual
    heat_demand = container['H_DEMAND_YCRA'].records
    heat_areas = set(heat_demand.loc[heat_demand[heat_demand.columns[-1]] > 0, 'AAA'])

    found = False
    for symbol in symbols:
        if symbol not in present:
            print(f"{symbol}: not in results")
            continue
        df = container[symbol].records
        if symbol == 'H_PRICE_YCRAST':
            df = df[df['AAA'].isin(heat_areas)]
        value = df.columns[-1]
        season = next(col for col in df.columns if df[col].astype(str).str.fullmatch(r'S\d+').all())
        high = df[df[value] > threshold]
        print(f"{symbol}: {len(high)} of {len(df)} entries above {threshold:g} (max {df[value].max():.3g})")
        if len(high):
            found = True
            print(f"  seasons: {' '.join(sorted(high[season].unique()))}")
    if found:
        warnings.warn("PRICES SET BY INFEASIBILITY PENALTIES - CHECK VQ* SLACKS IN all_endofmodel.gdx!")


@main.command()
@click.pass_context
@click.option('--gdx', type=str, default='', help="GDX to check [default: <sc-folder>/model/all_endofmodel.gdx]")
@click.option('--tolerance', type=float, default=1e-3, show_default=True,
              help="Level above which a slack counts as used - barrier noise is ~1e-9")
@click.option('--top', type=int, default=10, show_default=True, help="Number of largest locations to print per symbol")
@click.option('--fail-on', type=str, multiple=True,
              help="Only these slack variables fail the check, the rest are reported [default: all]. Repeatable")
@click.option('--fail-above', type=float, default=0, show_default=True,
              help="Fail only if a --fail-on variable's summed level exceeds this")
def slacks(ctx, gdx, tolerance, top, fail_on, fail_above):
    """
    Check that no slack variable is used - exits with status 1 if one is

    With --fail-on, only the listed variables fail the check, and only if
    their summed level is above --fail-above, and then exit with status 3,
    so a crash (status 1) can be told apart. The job scripts use this to
    stop on G2V infrastructure slack but not on the rolling CO2 slack that
    ADR 0060 expects.

    Lists every VQ* variable plus VG2VINFRASLACK and VHYDROGEN_QH2EQ with a
    level above the tolerance, by symbol, region and direction (IPLUSMINUS).
    Levels are in the symbol's own unit (MW or MWh per time step, t CO2 for
    VQLIMCO2NA/VQCCS_STORAGE). VQLIMCO2ROLLS is annualised like the rest of a
    rolling solve, so the week's tonnes are its level / 52 (ADR 0089). Each
    slack unit costs PENALTYQ (1e9) in QOBJ, a tonne of CO2 only 1e6, so the
    job scripts' check for objectives above 1e13 misses fewer than ~1e4 slack
    units or 10 Mt CO2 per solve (~0.2 Mt in a rolling week). Backup
    generation is cost, not slack - see the backup command.
    """

    sc_folder = ctx.obj['sc-folder']
    gdx = str(Path(gdx or f'{sc_folder}/model/all_endofmodel.gdx').absolute())
    print(f"Checking {gdx}")

    # Read only the slack variables - all_endofmodel.gdx is over 1 GB
    container = gt.Container(system_directory=GAMS_SYSTEM_DIR)
    container.read(gdx, records=False)
    symbols = [name for name in container.listVariables()
               if name.startswith('VQ') or name in ['VG2VINFRASLACK', 'VHYDROGEN_QH2EQ']]
    container = gt.Container(system_directory=GAMS_SYSTEM_DIR)
    container.read(gdx, symbols=symbols)

    # GROUP locates the CO2 limit slacks VQLIMCO2NA and VQLIMCO2ROLLS
    region_sets = ['C', 'CCC', 'IR', 'RRR', 'IA', 'AAA', 'CCCRRRAAA', 'IRRRE', 'IRRRI', 'GROUP']
    used = []
    for symbol in symbols:
        df = container[symbol].records
        if df is None:
            continue
        df = df[df['level'].abs() > tolerance]
        if df.empty:
            continue
        used.append(symbol)
        dims = container[symbol].domain_labels
        where = [dim for dim in dims if dim in region_sets or dim == 'IPLUSMINUS']
        print(f"\n{symbol}: {len(df)} entries above {tolerance:g} "
              f"(sum {df['level'].sum():.4g}, max {df['level'].max():.4g})")
        if where:
            by_location = (
                df
                .groupby(where, observed=True)['level']
                .agg(['count', 'sum', 'max'])
                .sort_values('sum', ascending=False)
            )
            print(by_location.head(top).to_string(float_format='{:.4g}'.format))
            if len(by_location) > top:
                print(f"... {len(by_location) - top} more")

    if used:
        print(f"\n{len(used)} slack variables used: {' '.join(used)}")
        if not fail_on:
            ctx.exit(1)
        failed = [symbol for symbol in used if symbol in fail_on
                  and container[symbol].records['level'].sum() > fail_above]
        if failed:
            print(f"Above --fail-above {fail_above:g}: {' '.join(failed)}")
            ctx.exit(3)
        print(f"None of {' '.join(fail_on)} sums above {fail_above:g}")
        return
    print(f"No slack variable above {tolerance:g} ({len(symbols)} checked)")


@main.command()
@click.pass_context
@click.option('--scenario', type=str, default='', help="Check a specific MainResults file in the folder")
@click.option('--fail-above', type=float, default=None,
              help="Exit with status 1 if backup generation in a year exceeds this (TWh) [default: report only]")
def backup(ctx, scenario, fail_above):
    """
    Report production of the backup generators (GNR_BACKUP_*) by country

    Backup generators (ADDBACKUPGEN) cover unserved electricity, heat,
    hydrogen and biomethane demand at a high variable cost (GDOMVCOST0 up to
    3000 money/MWh). That is cost, not slack, so neither the job scripts'
    objective check nor the slacks command sees it. Prints PRO_YCRAGF by
    year, country and commodity (TWh).
    """

    sc_folder = ctx.obj['sc-folder']
    res = find_result(sc_folder, scenario, GAMS_SYSTEM_DIR)
    print(f"Checking {Path(res.paths[0], res.files[0])}")

    df = res.get_result('PRO_YCRAGF')
    df = df[df.Generation.str.startswith('GNR_BACKUP')]
    if df.empty:
        print("No backup generation")
        return

    by_country = df.pivot_table(index=['Year', 'Country'], columns='Commodity', values='Value',
                                aggfunc='sum', fill_value=0, observed=True)
    shown = by_country[by_country.sum(axis=1) >= 1e-3]
    total = df.groupby('Year', observed=True).Value.sum()
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 250):
        print(shown.round(3))
    if len(shown) < len(by_country):
        print(f"({len(by_country) - len(shown)} year-countries below 0.001 TWh not shown)")
    print("\nTotal backup generation (TWh): " + ", ".join(f"{year} {value:.3f}" for year, value in total.items()))
    warnings.warn("BACKUP GENERATORS PRODUCE - UNSERVED DEMAND COVERED AT PENALTY COST!")
    if fail_above is not None and (total > fail_above).any():
        ctx.exit(1)


@main.command()
@click.pass_context
@click.option('--scenario', type=str, default='', help="Check a specific MainResults file in the folder")
@click.option('--gdx', type=str, default='',
              help="GDX holding CCS_STORAGE_MAX and CCS_TRANSPORTCOST [default: <sc-folder>/model/all_endofmodel.gdx]")
@click.option('--tolerance', type=float, default=1e-3, show_default=True, help="Relative tolerance above the limit")
@click.option('--top', type=int, default=10, show_default=True, help="Number of largest capturing countries to print per year")
def ccs_storage(ctx, scenario, gdx, tolerance, top):
    """
    Check captured CO2 against the storage limit - exits with status 1 if above

    QCCS_STORAGE caps the CO2 captured per year by all CCS_G (CCS_STORAGE_MAX,
    t CO2) in investment and fullyear runs only: rolling runs solve one season
    at a time, so the annual limit can't be an equation there. This checks the
    rolling result afterwards. MainResults has no captured-CO2 symbol, so the
    captured tonnes are the CO2 transport cost (OBJ_YCR
    GENERATION_CO2_TRANSPORT, Mmoney) divided by CCS_TRANSPORTCOST, which
    QOBJ charges per tonne captured. See GREAT docs/adr/0084.
    """

    sc_folder = ctx.obj['sc-folder']
    res = find_result(sc_folder, scenario, GAMS_SYSTEM_DIR)
    gdx = str(Path(gdx or f'{sc_folder}/model/all_endofmodel.gdx').absolute())
    print(f"Checking {Path(res.paths[0], res.files[0])} against {gdx}")

    container = gt.Container(system_directory=GAMS_SYSTEM_DIR)
    container.read(gdx, records=False)
    if 'CCS_STORAGE_MAX' not in container:
        print("CCS_STORAGE_MAX not in the GDX - run predates the storage limit")
        ctx.exit(1)
    container = gt.Container(system_directory=GAMS_SYSTEM_DIR)
    container.read(gdx, symbols=['CCS_STORAGE_MAX', 'CCS_TRANSPORTCOST'])
    limit = container['CCS_STORAGE_MAX'].records
    limit = limit.set_index(limit.columns[0])[limit.columns[-1]] / 1e6
    transport_cost = container['CCS_TRANSPORTCOST'].toValue()

    df = res.get_result('OBJ_YCR')
    df = df[df.Category == 'GENERATION_CO2_TRANSPORT']
    if df.empty:
        print("No CO2 captured")
        return
    # Mmoney / (money/t) = Mt
    df = df.assign(Value=df.Value / transport_cost)

    above = False
    for year, captured in df.groupby('Year', observed=True):
        total = captured.Value.sum()
        cap = limit.get(str(year))
        if cap is None:
            print(f"\n{year}: {total:.2f} Mt captured, no limit")
            continue
        exceeded = total > cap * (1 + tolerance)
        above |= exceeded
        print(f"\n{year}: {total:.2f} Mt captured, limit {cap:.2f} Mt ({total / cap:.1%})"
              + (" - ABOVE THE LIMIT" if exceeded else ""))
        by_country = captured.groupby('Country', observed=True).Value.sum().sort_values(ascending=False)
        print(by_country[by_country > 0].head(top).to_string(float_format='{:.2f}'.format))

    if above:
        warnings.warn("CAPTURED CO2 ABOVE THE STORAGE LIMIT CCS_STORAGE_MAX!")
        ctx.exit(1)


if __name__ == '__main__':
    main()
