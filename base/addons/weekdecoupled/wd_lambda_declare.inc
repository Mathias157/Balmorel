* WeekDecoupled add-on (docs/adr/0006): shadow prices of the annual limits.
* Written by any run with export_results (wd_export.inc) and read by a WeekDecoupled run
* (wd_beforeloop.inc), so both include this file and it declares only once.
* Units: money per unit of the limit, undiscounted (the objective's year weight is divided out).

$if not declared WDLAMBDA_CO2NA PARAMETER WDLAMBDA_CO2NA(YYY,GROUP)         "Shadow price of the annual CO2 limit QLIMCO2NA (money/t)";
$if not declared WDLAMBDA_CCS   PARAMETER WDLAMBDA_CCS(YYY)                 "Shadow price of the annual CO2 storage limit QCCS_STORAGE (money/t)";
$if not declared WDLAMBDA_GMAXF PARAMETER WDLAMBDA_GMAXF(YYY,CCCRRRAAA,FFF) "Shadow price of the annual fuel limits QGMAXCF, QGMAXRF and QGMAXAF (money/GJ)";
