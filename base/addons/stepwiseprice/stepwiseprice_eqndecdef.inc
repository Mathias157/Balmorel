Equations
   QSTEPWISEPRICE_GFTOSTEP(Y,C,FFF)                'Fuel usage in each country fixed to stepwise variable'
   QSTEPWISEPRICE_GFSTEP(Y,C,STEPWISEPRICE_L,FFF)         'Fuel usage on each line segment does not exceed max limit in energy'
;

QSTEPWISEPRICE_GFTOSTEP(IY411,C,STEPWISEPRICE_FFF)$(ISTEPWISEPRICE_F(IY411,C,STEPWISEPRICE_FFF) AND SUM((IA,G)$(IGF(G,STEPWISEPRICE_FFF) AND ICA(C,IA)),IAGK_HASORPOT(IY411,IA,G))) ..
   SUM(STEPWISEPRICE_L, VSTEPWISEPRICE_VGF_T_STEP(IY411,C,STEPWISEPRICE_L,STEPWISEPRICE_FFF))

         =e=
   SUM(IA$ICA(C,IA),
         SUM(G$(IAGK_HASORPOT(IY411,IA,G) AND (IGF(G,STEPWISEPRICE_FFF))),SUM((IS3,T), IHOURFRAC*IHOURSINST(IS3,T) * VGF_T(IY411,IA,G,IS3,T)))
    )
;

QSTEPWISEPRICE_GFSTEP(IY411,C,STEPWISEPRICE_L,STEPWISEPRICE_FFF)$ISTEPWISEPRICE_F(IY411,C,STEPWISEPRICE_FFF)..
   IOF3P6*VSTEPWISEPRICE_VGF_T_STEP(IY411,C,STEPWISEPRICE_L,STEPWISEPRICE_FFF)
         =l=
   STEPWISEPRICE_AMOUNT(IY411,C,STEPWISEPRICE_L,STEPWISEPRICE_FFF)
;


