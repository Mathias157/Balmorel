Equations
   QHYDROGEN_HGEHTOH2(Y,AAA,G,S,T)    'Link heat and electricity demand of technologies consuming heat and electricity to produce H2'
   QHYDROGEN_HGETOHH2(Y,AAA,G,S,T)    'Link electricity demand of technologies consuming electricity to produce H2 and heat'
   QHYDROGEN_H2TOEH(Y,AAA,G,S,T)      'Link heat and electricity in technologies consuming hydrogen and producing heat and electricity'
   QHYDROGEN_GCH4KT_UP(Y,AAA,G,S,T)   'Hydrogen production of steam reforming plants restricted by capacity'
   QHYDROGEN_STOVOL(Y,AAA,G,S,T)      'Dynamic equation hydrogen storage'
   QHYDROGEN_STOMAXCON(Y,AAA,G,S,T)   'Maximum hydrogen storage capacity'
   QHYDROGEN_STOMAXLOAD(Y,AAA,G,S,T)  'Maximum loading capacity of hydrogen storage'
   QHYDROGEN_STOMAXUNLD(Y,AAA,G,S,T)  'Maximum unloading capacity of hydrogen storage'
   QHYDROGEN_EQ(Y,RRR,S,T)            'Hydrogen production equal demand'
   QHYDROGEN_EQ_AREA(Y,AAA,S,T)       'Hydrogen production equals demand at an areal level'
   QHYDROGENGKE_UP_ADD(Y,AAA,G,S,T)   'Capacity adjustment constraint on electricity generation from biogas upgraded plants (MW)'
   QBIOMETHANE_EQ(Y,S,T)              'Biomethane production equals demand on international level in each year'
   QBIOMETHANE_STOVOLTS(Y,S,T)        'Dynamic equation biomethane storage'
   QGKBIOGASUPGRADING_UP(Y,AAA,G,S,T)  'Maximum generation of biomethane from biogas upgrading restricted by capacity (MW)'
   QGKBIOGASMETHANATION_UP(Y,AAA,G,S,T)  'Maximum generation of biomethane via biogas methanation restricted by capacity (MW)'
   QGKBIOMETHANE_UP(Y,AAA,G,S,T)      'Maximum generation of SNG restricted by capacity (MW)'
;



QHYDROGEN_HGEHTOH2(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GEHTOH2),IS3,T)$GDATA(IHYDROGEN_GEHTOH2,'GDCB')..

       VGE_T(IY411,IA,IHYDROGEN_GEHTOH2,IS3,T) =E= VGH_T(IY411,IA,IHYDROGEN_GEHTOH2,IS3,T)*GDATA(IHYDROGEN_GEHTOH2,'GDCB');

QHYDROGEN_HGETOHH2(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GETOHH2),IS3,T)$GDATA(IHYDROGEN_GETOHH2,'GDCB')..

       VGE_T(IY411,IA,IHYDROGEN_GETOHH2,IS3,T) =E= VGH_T(IY411,IA,IHYDROGEN_GETOHH2,IS3,T)*GDATA(IHYDROGEN_GETOHH2,'GDCB');


QHYDROGEN_H2TOEH(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2TOEH),IS3,T)$GDATA(IHYDROGEN_GH2TOEH,'GDCB')..

       VGE_T(IY411,IA,IHYDROGEN_GH2TOEH,IS3,T) =E= VGH_T(IY411,IA,IHYDROGEN_GH2TOEH,IS3,T)*GDATA(IHYDROGEN_GH2TOEH,'GDCB');

* Hydrogen gas storage, dynamic balance for weekly time horizon:
* Start and end filling degree in each week fixed to values obtained
* from yearly simulation


* Hydrogen production equal demand on region level:
* Prod + OutputStorage - InputStorage = DemandTransport + DemandPower+DemandBioRefinery + other

QHYDROGEN_EQ(IY411,IR,IS3,T)..
   SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GETOH2)$(RRRAAA(IR,IA)),VGE_T(IY411,IA,IHYDROGEN_GETOH2,IS3,T)*GDATA(IHYDROGEN_GETOH2,'GDFE')) +
   SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GETOHH2)$(RRRAAA(IR,IA)),VGE_T(IY411,IA,IHYDROGEN_GETOHH2,IS3,T)*GDATA(IHYDROGEN_GETOHH2,'GDFE'))+
   SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GEHTOH2)$(RRRAAA(IR,IA)),VGE_T(IY411,IA,IHYDROGEN_GEHTOH2,IS3,T)*GDATA(IHYDROGEN_GEHTOH2,'GDFE'))+
   SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GCH4TOH2)$(RRRAAA(IR,IA)),VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GCH4TOH2,IS3,T)) +
   SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO)$(RRRAAA(IR,IA)),VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GH2STO,IS3,T))
   - SUM((IA,IHYDROGEN_GH2STO)$(RRRAAA(IR,IA) AND (IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO))),VHYDROGEN_STOLOADT(IY411,IA,IHYDROGEN_GH2STO,IS3,T))
   =E=
   IHYDROGEN_DH2_REGION_T_Y(IY411,IR,IS3,T)/(1-DISLOSS_H2(IR))+
   SUM(IA$RRRAAA(IR,IA),IHYDROGEN_DH2_AREA_T_Y(IY411,IA,IS3,T)/(1-DISLOSS_H2(IA)))
   + SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2FUEL)$(RRRAAA(IR,IA)),VGE_T(IY411,IA,IHYDROGEN_GH2FUEL,IS3,T)/GDATA(IHYDROGEN_GH2FUEL,'GDFE'))
    + SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2TOBIOMETH)$(RRRAAA(IR,IA)),VGBIOMETH_T(IY411,IA,IHYDROGEN_GH2TOBIOMETH,IS3,T)/GDATA(IHYDROGEN_GH2TOBIOMETH,'GDFE'))
  + SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)$(RRRAAA(IR,IA)),VGBIOGASMETHANATION_T(IY411,IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T)*METHANATION_DH2(IHYDROGEN_GBIOGASMETHANATION))

- (SUM(IRE$IXH2K_HASORPOT(IY411,IRE,IR), VXH2_T(IY411,IRE,IR,IS3,T)*(1-XH2LOSS(IRE,IR))))                      !! Import to IR
+ (SUM(IRI$IXH2K_HASORPOT(IY411,IR,IRI), VXH2_T(IY411,IR,IRI,IS3,T)))                                          !! Export from IR


$include "../../base/addons/_hooks/qhydrogen_eq.inc"

;

* Hydrogen production equal demand on area level:
* Prod + OutputStorage - InputStorage = DemandTransport + DemandPower + DemandBioRefinery + other

QHYDROGEN_EQ_AREA(IY411,IA,IS3,T)$HYDROGEN_DH2(IY411,IA)..
   SUM(IHYDROGEN_GETOH2$IAGK_HASORPOT(IY411,IA,IHYDROGEN_GETOH2),VGE_T(IY411,IA,IHYDROGEN_GETOH2,IS3,T)*GDATA(IHYDROGEN_GETOH2,'GDFE')) +
   SUM(IHYDROGEN_GETOHH2$IAGK_HASORPOT(IY411,IA,IHYDROGEN_GETOHH2),VGE_T(IY411,IA,IHYDROGEN_GETOHH2,IS3,T)*GDATA(IHYDROGEN_GETOHH2,'GDFE'))+
   SUM(IHYDROGEN_GEHTOH2$IAGK_HASORPOT(IY411,IA,IHYDROGEN_GEHTOH2),VGE_T(IY411,IA,IHYDROGEN_GEHTOH2,IS3,T)*GDATA(IHYDROGEN_GEHTOH2,'GDFE')) +
   SUM(IHYDROGEN_GCH4TOH2$IAGK_HASORPOT(IY411,IA,IHYDROGEN_GCH4TOH2),VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GCH4TOH2,IS3,T)) +
   SUM(IHYDROGEN_GH2STO$IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO), VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GH2STO,IS3,T))
   - SUM(IHYDROGEN_GH2STO$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO)),VHYDROGEN_STOLOADT(IY411,IA,IHYDROGEN_GH2STO,IS3,T))
   =E=
   IHYDROGEN_DH2_AREA_T_Y(IY411,IA,IS3,T)/(1-DISLOSS_H2(IA))
   + SUM(IHYDROGEN_GH2FUEL$IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2FUEL),VGE_T(IY411,IA,IHYDROGEN_GH2FUEL,IS3,T)/GDATA(IHYDROGEN_GH2FUEL,'GDFE'))
   + SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2TOBIOMETH),VGBIOMETH_T(IY411,IA,IHYDROGEN_GH2TOBIOMETH,IS3,T)/GDATA(IHYDROGEN_GH2TOBIOMETH,'GDFE'))
   + SUM(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GBIOGASMETHANATION),VGBIOGASMETHANATION_T(IY411,IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T)*METHANATION_DH2(IHYDROGEN_GBIOGASMETHANATION))

$include "../../base/addons/_hooks/qhydrogen_eq_area.inc"
;

* Hydrogen production from steam reforming restricted by capacity
QHYDROGEN_GCH4KT_UP(IY411,IA,IHYDROGEN_GCH4TOH2,IS3,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GCH4TOH2) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GCH4TOH2)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GCH4TOH2)))..
        VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GCH4TOH2,IS3,T) =L=
        (GKFX(IY411,IA,IHYDROGEN_GCH4TOH2)
$ifi %DECOM%==yes   -VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GCH4TOH2)$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GCH4TOH2)
        +VGKNACCUMNET(IY411,IA,IHYDROGEN_GCH4TOH2)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GCH4TOH2)))*(1$(NOT IGKRATE(IA,IHYDROGEN_GCH4TOH2,IS3,T)) + IGKRATE(IA,IHYDROGEN_GCH4TOH2,IS3,T))
;


QHYDROGEN_STOVOL(IY411,IA,IHYDROGEN_GH2STO,S,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO) AND IS3(S))..
    VHYDROGEN_STOVOL_T(IY411,IA,IHYDROGEN_GH2STO,S,T)
  + CHRONOHOUR(S,T)*(VHYDROGEN_STOLOADT(IY411,IA,IHYDROGEN_GH2STO,S,T) - VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GH2STO,S,T)/GDATA(IHYDROGEN_GH2STO,'GDFE'))
  + ((VHYDROGEN_STOVOL_T(IY411,IA,IHYDROGEN_GH2STO,S,T) + CHRONOHOUR(S,T)*(VHYDROGEN_STOLOADT(IY411,IA,IHYDROGEN_GH2STO,S,T) - VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GH2STO,S,T)/GDATA(IHYDROGEN_GH2STO,'GDFE'))
   - SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VHYDROGEN_STOVOL_T(IY411,IA,IHYDROGEN_GH2STO,S,ITALIAS))
    )*(SSIZE(S)-1))$(ORD(T) EQ CARD(T))
    =E=
       VHYDROGEN_STOVOL_T(IY411,IA,IHYDROGEN_GH2STO,S,T+1) +SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VHYDROGEN_STOVOL_T(IY411,IA,IHYDROGEN_GH2STO,S++1,ITALIAS))$(CARD(T) EQ ORD(T))

$include "../../base/addons/_hooks/qhydrogen_stovol.inc"
;

*Hydrogen storage is modelled as a inter-seasonal storage that can be used with a T resolutions
QHYDROGEN_STOMAXCON(IY411,IA,IHYDROGEN_GH2STO,S,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2STO)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2STO)) AND (IS3(S) OR (IS3(S-1) AND (ORD(T) EQ 1))))..
     GKFX(IY411,IA,IHYDROGEN_GH2STO)
   + VGKNACCUMNET(IY411,IA,IHYDROGEN_GH2STO)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2STO))
$ifi %DECOM%==yes   -VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GH2STO)$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2STO)
    =G=
   VHYDROGEN_STOVOL_T(IY411,IA,IHYDROGEN_GH2STO,S,T)
;

* Maximum loading, hydrogen gas storage:
QHYDROGEN_STOMAXLOAD(IY411,IA,IHYDROGEN_GH2STO,IS3,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2STO)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2STO)))..
   (   GKFX(IY411,IA,IHYDROGEN_GH2STO)/GDATA(IHYDROGEN_GH2STO,'GDSTOHLOAD')
   + (VGKNACCUMNET(IY411,IA,IHYDROGEN_GH2STO)/GDATA(IHYDROGEN_GH2STO,'GDSTOHLOAD'))$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2STO))
$ifi %DECOM%==yes   -(VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GH2STO)/GDATA(IHYDROGEN_GH2STO,'GDSTOHLOAD'))$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2STO)
   ) *(1$(NOT IGKRATE(IA,IHYDROGEN_GH2STO,IS3,T)) + IGKRATE(IA,IHYDROGEN_GH2STO,IS3,T))
    =G= VHYDROGEN_STOLOADT(IY411,IA,IHYDROGEN_GH2STO,IS3,T)
;

* Maximum unloading, hydrogen gas storage:
QHYDROGEN_STOMAXUNLD(IY411,IA,IHYDROGEN_GH2STO,IS3,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2STO) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2STO)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2STO)))..
   (   GKFX(IY411,IA,IHYDROGEN_GH2STO)/GDATA(IHYDROGEN_GH2STO,'GDSTOHUNLD')
   + (VGKNACCUMNET(IY411,IA,IHYDROGEN_GH2STO)/GDATA(IHYDROGEN_GH2STO,'GDSTOHUNLD'))$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2STO))
$ifi %DECOM%==yes   -(VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GH2STO)/GDATA(IHYDROGEN_GH2STO,'GDSTOHUNLD'))$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2STO)
   ) *(1$(NOT IGKRATE(IA,IHYDROGEN_GH2STO,IS3,T)) + IGKRATE(IA,IHYDROGEN_GH2STO,IS3,T))
    =G=
   VHYDROGEN_GH2_T(IY411,IA,IHYDROGEN_GH2STO,IS3,T)
;

QBIOMETHANE_EQ(IY411,IS3,T)$SUM((IA,IGBIOMETHANE),IAGK_HASORPOT(IY411,IA,IGBIOMETHANE))..

*Production SYNTHETIC NATURAL GAS
    + SUM((C,IA,IHYDROGEN_GH2TOBIOMETH)$(ICA(C,IA) AND IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2TOBIOMETH)),VGBIOMETH_T(IY411,IA,IHYDROGEN_GH2TOBIOMETH,IS3,T))
*Production BIOGAS METHANATION
   + SUM((C,IA,IHYDROGEN_GBIOGASMETHANATION)$(ICA(C,IA) AND IAGK_HASORPOT(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)),VGBIOGASMETHANATION_T(IY411,IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T))
*Production BIOGAS UPGRADING
   + SUM((C,IA,IHYDROGEN_GBIOGASUPGRADING)$(ICA(C,IA) AND IAGK_HASORPOT(IY411,IA,IHYDROGEN_GBIOGASUPGRADING)),VGBIOGASUPGRADING_T(IY411,IA,IHYDROGEN_GBIOGASUPGRADING,IS3,T))

    + VBIOMETH_STOUNLOADT(IY411,IS3,T)
  =E=

*Demand biomethane
     SUM((C,IA,IGBIOMETHANE)$(ICA(C,IA) AND IAGK_HASORPOT(IY411,IA,IGBIOMETHANE)),VGF_T(IY411,IA,IGBIOMETHANE,IS3,T))
    +  VBIOMETH_STOLOADT(IY411,IS3,T)
*$include "../../base/addons/_hooks/qbiomethane_eq.inc"
;


QBIOMETHANE_STOVOLTS(IY411,S,T)$(SUM((IA,IGBIOMETHANE),IAGK_HASORPOT(IY411,IA,IGBIOMETHANE)) AND IS3(S))..
      VBIOMETHSTOVOLTS(IY411,S,T)
    + CHRONOHOUR(S,T)*(VBIOMETH_STOLOADT(IY411,S,T) - VBIOMETH_STOUNLOADT(IY411,S,T))

+ (
    ( VBIOMETHSTOVOLTS(IY411,S,T)
    + CHRONOHOUR(S,T)*(VBIOMETH_STOLOADT(IY411,S,T) - VBIOMETH_STOUNLOADT(IY411,S,T))
    - SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VBIOMETHSTOVOLTS(IY411,S,ITALIAS))
   )*(SSIZE(S)-1)
  )$(ORD(T) EQ CARD(T))

  =E=

       VBIOMETHSTOVOLTS(IY411,S,T+1) +SUM(ITALIAS$(ORD(ITALIAS) EQ 1),VBIOMETHSTOVOLTS(IY411,S++1,ITALIAS))$(CARD(T) EQ ORD(T))

$include "../../base/addons/_hooks/qbiomethane_stovolts.inc"

;

QGKBIOGASUPGRADING_UP(IY411,IA,IHYDROGEN_GBIOGASUPGRADING,IS3,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GBIOGASUPGRADING) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GBIOGASUPGRADING)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GBIOGASUPGRADING)))..
        VGBIOGASUPGRADING_T(IY411,IA,IHYDROGEN_GBIOGASUPGRADING,IS3,T) =L=
        (GKFX(IY411,IA,IHYDROGEN_GBIOGASUPGRADING)
$ifi %DECOM%==yes   -VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GBIOGASUPGRADING)$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GBIOGASUPGRADING)
        +VGKNACCUMNET(IY411,IA,IHYDROGEN_GBIOGASUPGRADING)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GBIOGASUPGRADING)))*(1$(NOT IGKRATE(IA,IHYDROGEN_GBIOGASUPGRADING,IS3,T)) + IGKRATE(IA,IHYDROGEN_GBIOGASUPGRADING,IS3,T))
;

QGKBIOGASMETHANATION_UP(IY411,IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GBIOGASMETHANATION) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GBIOGASMETHANATION)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)))..
        VGBIOGASMETHANATION_T(IY411,IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T) =L=
        (GKFX(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)
$ifi %DECOM%==yes   -VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)
        +VGKNACCUMNET(IY411,IA,IHYDROGEN_GBIOGASMETHANATION)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GBIOGASMETHANATION)))*(1$(NOT IGKRATE(IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T)) + IGKRATE(IA,IHYDROGEN_GBIOGASMETHANATION,IS3,T))
;

QGKBIOMETHANE_UP(IY411,IA,IHYDROGEN_GH2TOBIOMETH,IS3,T)$(IAGK_HASORPOT(IY411,IA,IHYDROGEN_GH2TOBIOMETH) AND (SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2TOBIOMETH)) OR IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2TOBIOMETH)))..
        VGBIOMETH_T(IY411,IA,IHYDROGEN_GH2TOBIOMETH,IS3,T) =L=
        (GKFX(IY411,IA,IHYDROGEN_GH2TOBIOMETH)
$ifi %DECOM%==yes   -VDECOM_EXO_ACCUM(IY411,IA,IHYDROGEN_GH2TOBIOMETH)$IGDECOMEXOPOT(IY411,IA,IHYDROGEN_GH2TOBIOMETH)
        +VGKNACCUMNET(IY411,IA,IHYDROGEN_GH2TOBIOMETH)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IAGKNY(Y,IA,IHYDROGEN_GH2TOBIOMETH)))*(1$(NOT IGKRATE(IA,IHYDROGEN_GH2TOBIOMETH,IS3,T)) + IGKRATE(IA,IHYDROGEN_GH2TOBIOMETH,IS3,T))
;

*Hydrogen pipe transmission

EQUATIONS
QXH2K_UP(Y,IRRRE,IRRRI,S,T)           "H2 transmission capacity constraint (MW)"
QXH2KNACCUMNET(Y,IRRRE,IRRRI)         "NOT FINISHED, TODO, Accumulated new H2 transmission investments available at beginning of next year (MW)"
QXH2KNACCUMNET_NGTOH2(Y,IRRRE,IRRRI)  "NOT FINISHED, TODO, Accumulated new investments in conversion of existing natural gas pipe to H2 transmission available at beginning of next year (MW)"
QXH2INVSYMMETRY(Y,IRRRE,IRRRI)        "H2 Transmission investments are set symetric(MW)"
QXH2INVSYMMETRY_NGTOH2(Y,IRRRE,IRRRI) "Conversion of existing natural gas pipe to H2 Transmission investments are set symetric(MW)"
QXH2KMAX_NGTOH2(Y,IRRRE,IRRRI)        "Maximum conversion of existing natural gas pipe to H2 transmission capacity between regions"
*Equations for modelling economy of scale
QVXH2KN_ES(YYY,IRRRE,IRRRI)  "Equation to ensure the proper H2 capacity when using SOS2 variables"
QXH2LAMBDA_ES(YYY,IRRRE,IRRRI) "Equation to ensure all the Lambda variables are equal to 1 for the same H2 transmission line"
;

*"H2 transmission capacity constraint (MW)"
QXH2K_UP(IY411,IRE,IRI,IS3,T)$(SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN(Y,IRE,IRI)) OR SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN_NGTOH2(Y,IRE,IRI)))..
   (  XH2KFX(IY411,IRE,IRI)
      + VXH2KNACCUMNET(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN(Y,IRE,IRI))
      + VXH2KNACCUMNET_NGTOH2(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN_NGTOH2(Y,IRE,IRI))
    )*(1$(NOT IXH2KRATE(IRE,IRI,IS3,T))+IXH2KRATE(IRE,IRI,IS3,T))
     =G=  VXH2_T(IY411,IRE,IRI,IS3,T)
;

*"NOT FINISHED, TODO, Accumulated new heat transmission investments available at beginning of next year (MW)"
QXH2KNACCUMNET(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN(Y,IRE,IRI))..
  VXH2KNACCUMNET(IY411,IRE,IRI)  !! End of this year's VXH2KNACCUMNET (available at beginning of next year)'
     =E=
  SUM(IY402$IY411PREVY(IY411,IY402), VXH2KNACCUMNET(IY402,IRE,IRI)$SUM(Y$(YVALUE(Y) LT YVALUE(IY411)),IXH2KN(Y,IRE,IRI))) + VXH2KN(IY411,IRE,IRI)$IXH2KN(IY411,IRE,IRI)  !! VXH2KNVACCUMNET available at end of previous(i.e., start of this) year PLUS investment during this year

;

*"NOT FINISHED, TODO, Accumulated new heat transmission investments available at beginning of next year (MW)"
QXH2KNACCUMNET_NGTOH2(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN_NGTOH2(Y,IRE,IRI))..
  VXH2KNACCUMNET_NGTOH2(IY411,IRE,IRI)  !! End of this year's VXH2KNACCUMNET (available at beginning of next year)'
     =E=
  SUM(IY402$IY411PREVY(IY411,IY402), VXH2KNACCUMNET_NGTOH2(IY402,IRE,IRI)$SUM(Y$(YVALUE(Y) LT YVALUE(IY411)),IXH2KN(Y,IRE,IRI))) + VXH2KN_NGTOH2(IY411,IRE,IRI)$IXH2KN_NGTOH2(IY411,IRE,IRI)  !! VXH2KNVACCUMNET_NGTOH2 available at end of previous(i.e., start of this) year PLUS investment during this year

;

* "Transmission investments are set symetric(MW)"
QXH2INVSYMMETRY(IY411,IRE,IRI)$IXH2KN(IY411,IRE,IRI)..
   VXH2KN(IY411,IRE,IRI)
         =E=
   VXH2KN(IY411,IRI,IRE)
;

* "Transmission investments are set symetric(MW)"
QXH2INVSYMMETRY_NGTOH2(IY411,IRE,IRI)$IXH2KN_NGTOH2(IY411,IRE,IRI)..
   VXH2KN_NGTOH2(IY411,IRE,IRI)
         =E=
   VXH2KN_NGTOH2(IY411,IRI,IRE)
;

*"Maximum H2 transmission capacity between regions"
QXH2KMAX_NGTOH2(IY411,IRE,IRI)$XH2MAXK_NGTOH2(IY411,IRE,IRI)..
    XH2MAXK_NGTOH2(IY411,IRE,IRI)
     =G=
    VXH2KNACCUMNET_NGTOH2(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXH2KN_NGTOH2(Y,IRE,IRI))
;


QVXH2KN_ES(IY411,IRE,IRI)$(IXH2KN(IY411,IRI,IRE) AND (IXH2KN_ES(IRE,IRI)))..
   VXH2KN(IY411,IRE,IRI) =E= SUM(XES,VXH2LAMBDA(IY411,IRE,IRI,XES)*XH2KN_ES(IRE,IRI,XES));

QXH2LAMBDA_ES(IY411,IRE,IRI)$(IXH2KN(IY411,IRI,IRE) AND (IXH2KN_ES(IRE,IRI)))..
  SUM(XES,VXH2LAMBDA(IY411,IRE,IRI,XES)) =E= 1;