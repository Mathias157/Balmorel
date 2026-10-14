* Latest revision 20180418 (hr)


$ifi %vqdebug%==yes   $setglobal equation qktechgroupr
$ifi %vqdebug%==yes   $include   "../../base/addons/vqdebug/bb4/vqdebug_equations.inc";

* Project-specific right-hand side additions (included after the TECHGROUPKPOT term)
$if     EXIST '../data/QKTECHGROUPR_ADDITIONS.inc' $INCLUDE         '../data/QKTECHGROUPR_ADDITIONS.inc';
$if not EXIST '../data/QKTECHGROUPR_ADDITIONS.inc' $if EXIST '../../base/data/QKTECHGROUPR_ADDITIONS.inc' $INCLUDE '../../base/data/QKTECHGROUPR_ADDITIONS.inc';


$label endoffile
