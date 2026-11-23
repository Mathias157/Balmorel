* WeekDecoupled add-on (docs/adr/0006): after the loop over the weeks.
* GAMS merges each solve into the variables, so every week keeps its own solution values
* and the results written after this file cover the whole year. Variables without a season
* index hold the last week's values.

IS3(S) = YES;
IS3_NEXT(S) = YES;
IS3_ONLYNEXT(S) = YES;

* VOBJ holds the last week's LP. The year's cost is C0 once plus each week's own cost;
* the prices of the annual limits are not a cost.
VOBJ.L = WDC0 + SUM(S, WDWEEK(S,'opex'));

* Next to MainResults_%scenario_name%.gdx (OUTPUT_SUMMARY.inc)
execute_unload "WeekDecoupled_%scenario_name%.gdx", WDWEEK, WDC0, WDC0MODELSTAT, WDCO2NA_S, WDCCS_S, WDGMAXF_S,
   WDLAMBDA_CO2NA, WDLAMBDA_CCS, WDLAMBDA_GMAXF, EMI_POLNA, IGMAXF
$ifi %CCS%==yes   , CCS_STORAGE_MAX
;
