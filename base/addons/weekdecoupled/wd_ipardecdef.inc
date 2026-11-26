* WeekDecoupled add-on (docs/adr/0006): one LP per week, storage cycling within the week,
* annual limits replaced by the investment run's shadow prices.

*-- Combinations that would link the weeks or need a full year in one LP --------------
$ifi not %BB4%==yes                  $abort "WeekDecoupled: BB4 only"
$ifi %RollingSeasons%==yes           $abort "WeekDecoupled and RollingSeasons exclude each other"
$ifi not %import_results%==yes       $abort "WeekDecoupled: needs import_results (capacities and WDLAMBDA.gdx from the investment run)"
$ifi %TechInvest%==yes               $abort "WeekDecoupled: investments must be off (TechInvest)"
$ifi %TransInvest%==yes              $abort "WeekDecoupled: investments must be off (TransInvest)"
$ifi %H2TransInvest%==yes            $abort "WeekDecoupled: investments must be off (H2TransInvest)"
$ifi %DECOM%==yes                    $abort "WeekDecoupled: decommissioning must be off (DECOM)"
$ifi not %HYRSBB123%==none           $abort "WeekDecoupled: hydro reservoirs cycle within each week, set HYRSBB123 none"
$ifi not %ADDESTOVOLTS%==none        $abort "WeekDecoupled: storage cycles within each week, set ADDESTOVOLTS none"
$ifi not %ADDHSTOVOLTS%==none        $abort "WeekDecoupled: storage cycles within each week, set ADDHSTOVOLTS none"
$ifi %HYDROGEN%==yes $ifi not %ADDH2STOVOLTS%==none      $abort "WeekDecoupled: storage cycles within each week, set ADDH2STOVOLTS none"
$ifi %HYDROGEN%==yes $ifi not %ADDBIOMETHSTOVOLTS%==none $abort "WeekDecoupled: storage cycles within each week, set ADDBIOMETHSTOVOLTS none"
$ifi %EV%==yes $ifi %EV_INTERSEASONAL%==yes              $abort "WeekDecoupled: EV batteries cycle within each week, EV_INTERSEASONAL must be off"
$ifi %UnitComm%==yes $ifi %SEASONALLINKUC%==yes          $abort "WeekDecoupled: SEASONALLINKUC links the weeks"
$ifi %UnitComm%==yes $ifi %PLANNED_MAINTENANCE%==yes     $abort "WeekDecoupled: planned maintenance (QUCMAINTMIN) is annual"
$ifi %STEPWISE_RAMPING%==yes $ifi %SEASONALLINKRAMPING%==yes $abort "WeekDecoupled: SEASONALLINKRAMPING links the weeks"
$ifi %TRANS_RAMP%==yes               $abort "WeekDecoupled: TRANS_RAMP links the weeks"
$ifi %OPTIFLOW%==yes                 $abort "WeekDecoupled: OptiFlow has annual rows"
$ifi %LIMITSFORFUELS%==yes           $abort "WeekDecoupled: LIMITSFORFUELS has annual rows"
$ifi %STEPWISEPRICE%==yes            $abort "WeekDecoupled: STEPWISEPRICE has annual rows"
$ifi %X3V%==yes                      $abort "WeekDecoupled: X3V has annual rows"
$ifi %TRANSPORT%==yes $ifi %ADDSEASONALTRANSPORTDEMAND%==yes $abort "WeekDecoupled: not tested with ADDSEASONALTRANSPORTDEMAND"

$include "../../base/addons/weekdecoupled/wd_lambda_declare.inc"

*-- What each weekly solve leaves behind ------------------------------------------------
SET WDATTR "Per-week records of a WeekDecoupled run"
   / modelstat   "Model status of the week's LP"
     solvestat   "Solver status of the week's LP"
     resgen      "Seconds generating the week's LP"
     resusd      "Seconds solving the week's LP"
     vobj        "VOBJ of the week's LP: WDC0 + opex + lambdacost (money, discounted as VOBJ)"
     lambdacost  "Annual limits priced at their shadow prices in the week (money, discounted as VOBJ)"
     opex        "The week's own cost: vobj - lambdacost - WDC0 (money, discounted as VOBJ)" /;

PARAMETER WDWEEK(SSS,WDATTR)                      "Per-week records of a WeekDecoupled run";
PARAMETER WDCO2NA_S(YYY,GROUP,SSS)                "Net CO2 emissions under QLIMCO2NA per week (t)";
PARAMETER WDCCS_S(YYY,SSS)                        "CO2 stored under QCCS_STORAGE per week (t)";
PARAMETER WDGMAXF_S(YYY,CCCRRRAAA,FFF,SSS)        "Fuel use under QGMAXCF, QGMAXRF and QGMAXAF per week (GJ)";
SCALAR    WDC0                                    "VOBJ with no week in the LP: the week-independent part of every week's VOBJ (money, discounted as VOBJ)" /0/;
SCALAR    WDC0MODELSTAT                           "Model status of the LP with no week" /0/;

*-- The weeks this run solves -------------------------------------------------------------
* Every week in S, unless the run's data folder lists them, e.g.
*    SET WDSOLVE(SSS) 'Weeks this run solves' / S01, S11, S21 /;
* Several runs with disjoint lists can share the weeks of one simulation. Each repeats the
* C0 solve and the costs that belong to no week; whoever merges them counts those once.
$if     exist '../data/WDSOLVE.inc' $include '../data/WDSOLVE.inc';
$if not exist '../data/WDSOLVE.inc' SET WDSOLVE(SSS) "Weeks this run solves: every week in S";
$if not exist '../data/WDSOLVE.inc' WDSOLVE(S) = YES;
