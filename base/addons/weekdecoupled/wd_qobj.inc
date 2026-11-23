* WeekDecoupled add-on (docs/adr/0006): the annual limits as prices, at the investment run's shadow prices.
* Only limits with a price enter, so a free VWD_ variable never has a cost without its defining row.
   + SUM(GROUP$(WDLAMBDA_CO2NA(Y,GROUP) AND EMI_POLNA(Y,GROUP,'LIM_CO2') AND (EMI_POLNA(Y,GROUP,'LIM_CO2') LT INF)), WDLAMBDA_CO2NA(Y,GROUP)*VWD_CO2NA(Y,GROUP))
   + SUM((C,FFF)$(WDLAMBDA_GMAXF(Y,C,FFF) AND IGMAXF(Y,C,FFF)), WDLAMBDA_GMAXF(Y,C,FFF)*VWD_GMAXF(Y,C,FFF))
   + SUM((IR,FFF)$(WDLAMBDA_GMAXF(Y,IR,FFF) AND IGMAXF(Y,IR,FFF)), WDLAMBDA_GMAXF(Y,IR,FFF)*VWD_GMAXF(Y,IR,FFF))
   + SUM((IA,FFF)$(WDLAMBDA_GMAXF(Y,IA,FFF) AND IGMAXF(Y,IA,FFF)), WDLAMBDA_GMAXF(Y,IA,FFF)*VWD_GMAXF(Y,IA,FFF))
$ifi %CCS%==yes   + (WDLAMBDA_CCS(Y)*VWD_CCS(Y))$(WDLAMBDA_CCS(Y) AND CCS_STORAGE_MAX(Y))
