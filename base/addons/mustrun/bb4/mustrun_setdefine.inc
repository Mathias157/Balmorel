* The must-run sets and floor are scenario data written by pybalmorel (must-run-floor); there is no base default.
SET MUSTRUN_ZONE                            'Zones with a must-run floor (countries or bidding zones)' %semislash%
$if not EXIST '../data/MUSTRUN_ZONE.inc' $abort 'MUSTRUN=yes needs ../data/MUSTRUN_ZONE.inc (pybalmorel must-run-floor)'
$INCLUDE '../data/MUSTRUN_ZONE.inc';
%semislash%;

SET MUSTRUN_ZONE_RRR(MUSTRUN_ZONE,RRR)      'Regions in each must-run zone' %semislash%
$if not EXIST '../data/MUSTRUN_ZONE_RRR.inc' $abort 'MUSTRUN=yes needs ../data/MUSTRUN_ZONE_RRR.inc (pybalmorel must-run-floor)'
$INCLUDE '../data/MUSTRUN_ZONE_RRR.inc';
%semislash%;

SET MUSTRUN_GROUP                           'Fuel groups with a must-run floor' %semislash%
$if not EXIST '../data/MUSTRUN_GROUP.inc' $abort 'MUSTRUN=yes needs ../data/MUSTRUN_GROUP.inc (pybalmorel must-run-floor)'
$INCLUDE '../data/MUSTRUN_GROUP.inc';
%semislash%;

SET MUSTRUN_GROUP_FFF(MUSTRUN_GROUP,FFF)    'Fuels in each must-run fuel group' %semislash%
$if not EXIST '../data/MUSTRUN_GROUP_FFF.inc' $abort 'MUSTRUN=yes needs ../data/MUSTRUN_GROUP_FFF.inc (pybalmorel must-run-floor)'
$INCLUDE '../data/MUSTRUN_GROUP_FFF.inc';
%semislash%;
