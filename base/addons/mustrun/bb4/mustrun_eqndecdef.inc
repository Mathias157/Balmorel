Equations
   QMUSTRUN(Y,MUSTRUN_ZONE,MUSTRUN_GROUP,SSS,TTT)   'Minimum electricity output per zone, fuel group and season, in every time step (MW)'
;

* The slack keeps the model feasible where the floor cannot be met, e.g. back-pressure CHP without a heat sink.
QMUSTRUN(IY411,MUSTRUN_ZONE,MUSTRUN_GROUP,IS3,T)$MUSTRUN_FLOOR(MUSTRUN_ZONE,MUSTRUN_GROUP,IS3)..
    SUM(IA$IMUSTRUN_ZONE_A(MUSTRUN_ZONE,IA),
       SUM(G$(IAGK_HASORPOT(IY411,IA,G) AND IMUSTRUN_G(MUSTRUN_GROUP,G)), VGE_T(IY411,IA,G,IS3,T)))
  + VMUSTRUN_SLACK(IY411,MUSTRUN_ZONE,MUSTRUN_GROUP,IS3,T)
    =G=
    MUSTRUN_FLOOR(MUSTRUN_ZONE,MUSTRUN_GROUP,IS3);
