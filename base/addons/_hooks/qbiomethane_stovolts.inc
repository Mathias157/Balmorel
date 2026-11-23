
$ifi %vqdebug%==yes   $setglobal equation qbiomethane_stovolts
$ifi %vqdebug%==yes   $include   "../../base/addons/vqdebug/bb4/vqdebug_equations.inc";

$ifi %import_results%==yes  $include   "../../base/addons/import_results/import_results_qbiomethane_stovolts.inc";
$ifi %WeekDecoupled%==yes  $include   "../../base/addons/weekdecoupled/wd_qbiomethane_stovolts.inc";

$label endoffile
