* WeekDecoupled add-on (docs/adr/0006): each week's use of the annual limits.
* The right-hand sides are the left-hand sides of the annual rows, which the model leaves out
* under WeekDecoupled (Balmorelbb4.inc, CCS_balbase4.inc). Keep them in step with those rows.
* There is a row for every limit, not only for limits with a shadow price, so the run can
* report the use of every limit for the recourse on overshoot.

EQUATION QWD_CO2NA(Y,GROUP)        "Net CO2 emissions under QLIMCO2NA in the solved week (t)";
EQUATION QWD_GMAXCF(Y,CCC,FFF)     "Fuel use under QGMAXCF in the solved week (GJ)";
EQUATION QWD_GMAXRF(Y,RRR,FFF)     "Fuel use under QGMAXRF in the solved week (GJ)";
EQUATION QWD_GMAXAF(Y,AAA,FFF)     "Fuel use under QGMAXAF in the solved week (GJ)";
$ifi %CCS%==yes EQUATION QWD_CCS(Y) "CO2 stored under QCCS_STORAGE in the solved week (t)";

* QLIMCO2NA without its hook: gross emissions less the CCS term the hook adds to the right-hand side
QWD_CO2NA(IY411,GROUP)$(EMI_POLNA(IY411,GROUP,'LIM_CO2') AND (EMI_POLNA(IY411,GROUP,'LIM_CO2') LT INF))..
      VWD_CO2NA(IY411,GROUP)
      =E=
      SUM(C,
         SUM((IA,G)$(IAGK_HASORPOT(IY411,IA,G) AND ICA(C,IA) AND GROUP_AAA(GROUP,IA)), SUM((IS3,T), IHOURSINST(IS3,T)*IHOURFRAC * (IM_CO2(G) * IOF0001) * IOF3P6 * VGF_T(IY411,IA,G,IS3,T)))
         )
$ifi %CCS%==yes  -(0
$ifi %CCS%==yes  $include "../../base/addons/CCS/bb4/CCS_qlimco2na.inc"
$ifi %CCS%==yes  )
;

QWD_GMAXCF(IY411,C,FFF)$IGMAXF(IY411,C,FFF)..
      VWD_GMAXF(IY411,C,FFF)
      =E=
      SUM(IAGK_HASORPOT(IY411,IA,G)$(IGF(G,FFF) AND ICA(C,IA)), IOF3P6 * SUM((IS3,T), IHOURSINST(IS3,T)*IHOURFRAC * VGF_T(IY411,IA,G,IS3,T)));

QWD_GMAXRF(IY411,IR,FFF)$IGMAXF(IY411,IR,FFF)..
      VWD_GMAXF(IY411,IR,FFF)
      =E=
      SUM(IAGK_HASORPOT(IY411,IA,G)$(IGF(G,FFF) AND RRRAAA(IR,IA)), IOF3P6 * SUM((IS3,T), IHOURSINST(IS3,T)*IHOURFRAC * VGF_T(IY411,IA,G,IS3,T)));

QWD_GMAXAF(IY411,IA,FFF)$IGMAXF(IY411,IA,FFF)..
      VWD_GMAXF(IY411,IA,FFF)
      =E=
      SUM(IAGK_HASORPOT(IY411,IA,G)$(IGF(G,FFF)), IOF3P6 * SUM((IS3,T), IHOURSINST(IS3,T)*IHOURFRAC * VGF_T(IY411,IA,G,IS3,T)));

$ifi not %CCS%==yes $goto wd_no_ccs
QWD_CCS(IY411)$CCS_STORAGE_MAX(IY411)..
      VWD_CCS(IY411)
      =E=
      SUM(C, SUM((IA,G)$(ICA(C,IA) AND IAGK_HASORPOT(IY411,IA,G) AND CCS_G(G)), SUM((IS3,T), IHOURSINST(IS3,T) * ((IM_CO2(G)+IM_CO2RE(G))*IHOURFRAC*IOF0001) * IOF3P6 * VGF_T(IY411,IA,G,IS3,T)*CCS_CO2CAPTEFF_G(G))));
$label wd_no_ccs
