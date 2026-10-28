PARAMETER MUSTRUN_FLOOR(MUSTRUN_ZONE,MUSTRUN_GROUP,SSS)   'Minimum electricity output of a fuel group in a zone, per season (MW)' %semislash%
$if not EXIST '../data/MUSTRUN_FLOOR.inc' $abort 'MUSTRUN=yes needs ../data/MUSTRUN_FLOOR.inc (pybalmorel must-run-floor)'
$INCLUDE '../data/MUSTRUN_FLOOR.inc';
%semislash%;

* The penalty defaults to 300 Money/MWh unless the scenario has ../data/MUSTRUN_PENALTY.inc (the default
* lives here because base/data is not versioned). It must exceed the marginal cost of every floored fuel
* group, or the model pays the penalty instead of running the plant. Where the slack is used and the
* floored output could still rise, the zone's price falls to marginal cost minus the penalty.
$if     EXIST '../data/MUSTRUN_PENALTY.inc' $INCLUDE '../data/MUSTRUN_PENALTY.inc';
$if not EXIST '../data/MUSTRUN_PENALTY.inc' SCALAR MUSTRUN_PENALTY 'Penalty on electricity output missing from a must-run floor (Money/MWh)' /300/;
