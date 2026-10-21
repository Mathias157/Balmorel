

$ifi %TRANSPORT%==yes       $include   "../../base/addons/transport/bb4/transport_de_var_tadditions.inc";
$ifi %INDIVUSERS%==yes       $include   "../../base/addons/indivusers/bb4/indivusers_de_var_tadditions.inc"; 

* Project-specific corrections to DE_VAR_T
$if     EXIST '../data/DE_VAR_T_ADDITIONS.inc' $INCLUDE         '../data/DE_VAR_T_ADDITIONS.inc';
$if not EXIST '../data/DE_VAR_T_ADDITIONS.inc' $if EXIST '../../base/data/DE_VAR_T_ADDITIONS.inc' $INCLUDE '../../base/data/DE_VAR_T_ADDITIONS.inc';









