$if     EXIST '../data/DR_DATAINPUT.inc' $INCLUDE         '../data/DR_DATAINPUT.inc';
$if not EXIST '../data/DR_DATAINPUT.inc' $INCLUDE '../../base/data/DR_DATAINPUT.inc';
%semislash%;


* Written by the investment run for the runs without investments (docs/adr/0056); with import_results it is declared there
$ifi not %import_results%==yes PARAMETER DRKN_ACCUMNET(YYY,AAA,DR_TECHNOLOGIES) 'Accumulated demand response capacity to be used in future runs (MW)';
