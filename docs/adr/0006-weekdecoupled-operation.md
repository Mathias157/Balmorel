---
status: accepted
---

# 6. WeekDecoupled: each week of an operational simulation as its own LP, annual limits as prices

An operational simulation with fixed capacities (`import_results`, investments off) is one LP over the whole year. At 12 time steps per week it takes about 6 h, nearly all of it barrier time, which grows faster than linearly with the LP's size. `RollingSeasons` solves one week at a time. It hands each week's end levels to the next week, though, needs the gdx files of a fullyear run, and splits the annual CO2 limit by `EMI_POLNA_S.gdx`. Given only an investment run's `simex`, that split sets the cap to 0 in every week the investment run did not model.

We added an option `WeekDecoupled` (`balopt.opt`, empty by default, so existing runs are unchanged; code in `addons/weekdecoupled`). It needs `import_results` and solves every week in `S` as its own LP, one after another in one GAMS process, straight from the investment run's `simex`:

- **Storage cycles within each week.** In the seasonal storage balances (`QESTOVOLTS`, `QHSTOVOLTS`, `QHYDROGEN_STOVOL`, `QBIOMETHANE_STOVOLTS`), the week's last time step links to the week's own first step, so no energy carries between weeks. In `QHYRSSEQ` the week's end volume is the week's start volume, so each week's hydro generation is at most that week's inflow (spill is still allowed).
- **Annual limits become prices.** The rows `QLIMCO2NA`, `QCCS_STORAGE` and `QGMAXCF`/`QGMAXRF`/`QGMAXAF` are left out of the weekly LPs. Rows `QWD_*` measure each week's use of every limit in `VWD_CO2NA`, `VWD_CCS` and `VWD_GMAXF`. The objective prices that use at the limit's shadow price λ from the investment run. A fuel cap of 0 (`IGMAXF` = EPS) is not priced but kept as the bound `VWD_GMAXF.UP = 0` in every week. It holds exactly week by week, since fuel use is never negative, and a cap the investment run never needed to bind has λ = 0, which would let every week burn a banned fuel. `wd_export.inc` writes λ to `simex/WDLAMBDA.gdx` in every run that exports results, as `-M/(IOF1_*IDISCOUNTFACTOR*IWEIGHTY)` of the row's marginal. The WeekDecoupled run reads it from `simex`.
- **Annual transport demand** is split over the weeks in proportion to their hours.
- **Costs.** `IHOURSINST` is unchanged, so each week's costs are its share of the year's. One LP with no week in it (`IS3`, `IS3_NEXT` and `IS3_ONLYNEXT` empty) is solved first. Its objective `WDC0` is the part of the objective that no week changes, chiefly fixed O&M of the fixed capacities. Each week's own cost is `opex = VOBJ − λ·use − WDC0`. After the loop, `VOBJ.L = WDC0 + Σ opex`, so it excludes λ.
- **Records.** `WeekDecoupled_<scenario>.gdx`, next to `MainResults`, holds the following:
  - each week's model and solver status, generation and solve seconds, `vobj`, `lambdacost` and `opex` (`WDWEEK`);
  - each week's use of each limit (`WDCO2NA_S`, `WDCCS_S`, `WDGMAXF_S`);
  - the limits themselves and λ.

  The caller charges recourse on whatever the weeks together use beyond a limit.

Options and data that link the weeks or need the year in one LP stop the run:

- At compile time:
  - `RollingSeasons`;
  - investment or decommissioning;
  - storage levels other than `none`;
  - `EV_INTERSEASONAL`;
  - the UC and ramping options that link seasons;
  - `TRANS_RAMP`, `OPTIFLOW`, `LIMITSFORFUELS`, `STEPWISEPRICE` and `X3V`.
- At run time:
  - more than one year in `Y`;
  - `GMINF`/`GEQF` and `FGEMIN`/`FGEMAX` limits;
  - finite CO2, SO2 or NOx limits in `EMI_POL` (use `EMI_POLNA`).

## Consequences

- **The run needs no fullyear run.** The capacities and λ come from the investment run's `simex`, and the model's fixed setup is paid once for all weeks. At 12 steps per week each weekly LP has about 55,000 rows and 149,000 columns. Generating it takes about 3.4 s, and barrier without crossover solves it in about 0.8 s (means over 52 weeks on a laptop, 2 threads). All 52 weeks took 11.5 min:
  - 6.4 min before the first solve, most of it EV preprocessing (`EV_ipardecdef.inc`), which grows with the number of weeks;
  - 4.1 min for the C0 solve and the weeks;
  - 0.8 min for output.

  A `RollingSeasons` run of the same weeks took 12.4 min.
- **Seasonal storage cannot shift energy between weeks**, and reservoirs only use each week's own inflow. The result is a valid dispatch for the year, but a more expensive one than the year-long LP's whenever seasonal storage matters.
- **Season-indexed results cover the whole year.** GAMS keeps each solve's levels, so `MainResults` and `all_endofmodel.gdx` hold every week's dispatch. Variables without a season index hold the last week's values. The marginals of the annual rows are not meaningful, and `balbase4.mss` shows only the last solve, so the run's statuses are in `WDWEEK`.
- **λ is only as good as the run that exported it.** With `vqdebug` and `VQCO2PRICE`, a CO2 limit the exporting run overshoots gives λ = `VQCO2PRICE`, the slack's price, not the limit's value. Barrier without crossover leaves λ of about 1e-9 on limits that do not bind. Such λ cost nothing.
- **`QWD_*` copy the left-hand sides of the annual rows**, so a change to `QLIMCO2NA`, `QCCS_STORAGE` or `QGMAX*F` must be made in `wd_eqndecdef.inc` too.
- **Weeks can run in parallel** by giving each GAMS process a subset of `S`. The fixed setup is then paid once per process.

## Considered Options

- **`RollingSeasons`**: rejected for the reasons above. With storage levels `none`, its end levels are free, so stored energy has no value and storage is drawn down myopically.
- **One LP with the annual limits kept exact**: rejected because it is the 6 h LP, and the limits are the only thing linking the weeks once storage cycles.
- **One GAMS process per week**: rejected as the default, because it pays the fixed setup once per week rather than once.
- **Splitting each limit over the weeks** (quotas by hours, or by the investment run's use per season): rejected. A quota that is wrong for a week makes that week's dispatch worse, with no way to trade between weeks. A price lets each week use what it is worth.
