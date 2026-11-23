* WeekDecoupled add-on (docs/adr/0006): shadow prices of the annual limits, for a later WeekDecoupled run.
* Every run that exports results writes them; a WeekDecoupled run reads them (wd_beforeloop.inc).
* A limit left out of the solved model has marginal 0, so its price is 0.

$ifi %WeekDecoupled%==yes $goto wd_export_end

$include "../../base/addons/weekdecoupled/wd_lambda_declare.inc"

WDLAMBDA_CO2NA(YYY,GROUP) = 0;
WDLAMBDA_CCS(YYY) = 0;
WDLAMBDA_GMAXF(YYY,CCCRRRAAA,FFF) = 0;

* Marginals of =L= rows are negative when the limit binds; divide out the objective's year weight
WDLAMBDA_CO2NA(Y,GROUP)$(QLIMCO2NA.M(Y,GROUP) LT 0) = -QLIMCO2NA.M(Y,GROUP)/(IOF1_*IDISCOUNTFACTOR(Y)*IWEIGHTY(Y));
WDLAMBDA_GMAXF(Y,C,FFF)$(QGMAXCF.M(Y,C,FFF) LT 0)   = -QGMAXCF.M(Y,C,FFF)/(IOF1_*IDISCOUNTFACTOR(Y)*IWEIGHTY(Y));
WDLAMBDA_GMAXF(Y,IR,FFF)$(QGMAXRF.M(Y,IR,FFF) LT 0) = -QGMAXRF.M(Y,IR,FFF)/(IOF1_*IDISCOUNTFACTOR(Y)*IWEIGHTY(Y));
WDLAMBDA_GMAXF(Y,IA,FFF)$(QGMAXAF.M(Y,IA,FFF) LT 0) = -QGMAXAF.M(Y,IA,FFF)/(IOF1_*IDISCOUNTFACTOR(Y)*IWEIGHTY(Y));
$ifi %CCS%==yes WDLAMBDA_CCS(Y)$(QCCS_STORAGE.M(Y) LT 0) = -QCCS_STORAGE.M(Y)/(IOF1_*IDISCOUNTFACTOR(Y)*IWEIGHTY(Y));

execute_unload "../simex/WDLAMBDA.gdx", WDLAMBDA_CO2NA, WDLAMBDA_CCS, WDLAMBDA_GMAXF;

$label wd_export_end
