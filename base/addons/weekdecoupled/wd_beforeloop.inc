* WeekDecoupled add-on (docs/adr/0006): before the loop over the weeks (Balmorelbb4.sim).
* This file runs inside the loop over IYALIAS, so it holds execution statements only.

* WDWEEK and the per-week outputs have no year index
abort$(CARD(Y) GT 1) "WeekDecoupled solves one model year only (docs/adr/0006)";

* WDSOLVE (wd_ipardecdef.inc) picks the weeks of S that this run solves
abort$(SUM(S$WDSOLVE(S), 1) EQ 0) "WeekDecoupled: WDSOLVE holds no week of S";
abort$SUM(SSS$(WDSOLVE(SSS) AND NOT S(SSS)), 1) "WeekDecoupled: WDSOLVE holds a week that is not in S";

* The annual rows WeekDecoupled leaves out without a price must have no data (Balmorelbb4.inc model list).
* The conditions are those of the rows.
abort$SUM((IY411,CCCRRRAAA,FFF)$(IGMINF(IY411,CCCRRRAAA,FFF) OR IGEQF(IY411,CCCRRRAAA,FFF)), 1)
   "WeekDecoupled: annual minimum or exact fuel use (GMINF, GEQF) has no weekly form (docs/adr/0006)";
abort$SUM((CCCRRRAAA,FFF)$(FGEMIN(CCCRRRAAA,FFF) OR FGEMAX(CCCRRRAAA,FFF)), 1)
   "WeekDecoupled: annual generation by fuel (FGEMIN, FGEMAX) has no weekly form (docs/adr/0006)";
abort$SUM((IY411,CCCRRRAAA,GROUP)$(
          (EMI_POL(IY411,CCCRRRAAA,GROUP,'LIM_CO2') AND (EMI_POL(IY411,CCCRRRAAA,GROUP,'LIM_CO2') LT INF))
       OR (EMI_POL(IY411,CCCRRRAAA,GROUP,'LIM_SO2') AND (EMI_POL(IY411,CCCRRRAAA,GROUP,'LIM_SO2') LT INF))
       OR (EMI_POL(IY411,CCCRRRAAA,GROUP,'LIM_NOX') AND (EMI_POL(IY411,CCCRRRAAA,GROUP,'LIM_NOX') LT INF))), 1)
   "WeekDecoupled: emission limits by country (EMI_POL) have no weekly form, use EMI_POLNA (docs/adr/0006)";

* Shadow prices of the annual limits, written by the investment run (wd_export.inc)
execute_load '../simex/WDLAMBDA.gdx', WDLAMBDA_CO2NA, WDLAMBDA_CCS, WDLAMBDA_GMAXF;

* A fuel cap of 0 (IGMAXF = EPS) holds exactly week by week, because fuel use is never negative.
* Such caps stay hard in every week instead of being priced: a cap the investment run never met
* has a price of 0, so a week would burn the fuel freely where the year-long LP may burn none.
VWD_GMAXF.UP(IY411,CCCRRRAAA,FFF)$(IGMAXF(IY411,CCCRRRAAA,FFF) AND (IGMAXF(IY411,CCCRRRAAA,FFF) LE 0)) = 0;

* C0: the part of the objective that belongs to no week, such as the fixed costs of the capacities.
* Every week's VOBJ holds it once, so it comes from one solve with no week at all.
IS3(S) = NO;
IS3_NEXT(S) = NO;
IS3_ONLYNEXT(S) = NO;

$ifi not %USEOPTIONFILE%==0 BALBASE4.optfile = %USEOPTIONFILE%;
$ifi %SOLVETYPE%==LP   SOLVE BALBASE4 USING LP   MINIMIZING VOBJ;
$ifi %SOLVETYPE%==RMIP SOLVE BALBASE4 USING RMIP MINIMIZING VOBJ;
$ifi %SOLVETYPE%==MIP  SOLVE BALBASE4 USING MIP  MINIMIZING VOBJ;

WDC0 = VOBJ.L;
WDC0MODELSTAT = BALBASE4.modelstat;
