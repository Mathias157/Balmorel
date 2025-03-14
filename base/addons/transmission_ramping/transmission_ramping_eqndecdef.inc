* Transmission ramping by Juan Gea Berm�dez 2019.

EQUATION QXRAMP1  "Total ramping in a line limited by maximum ramping. Equation 1 (MW)";
EQUATION QXRAMP2  "Total ramping in a line limited by maximum ramping. Equation 2 (MW)";


QXRAMP1(IY411,IRE,IRI,S,T)$((1 GT CHRONOHOUR(S,T)*X_RAMP*0.5) AND (NOT (ORD(S) EQ 1 AND (ORD(T) EQ 1))) AND IS3(S) AND IXK_HASORPOT(IY411,IRE,IRI))..
VX_T(IY411,IRE,IRI,S-1,T--1)$(ORD(T) EQ 1) + VX_T(IY411,IRE,IRI,S,T-1)$(NOT (ORD(T) EQ 1))
    - VX_T(IY411,IRE,IRI,S,T)

-VX_T(IY411,IRI,IRE,S-1,T--1)$(ORD(T) EQ 1) - VX_T(IY411,IRI,IRE,S,T-1)$(NOT (ORD(T) EQ 1))
    + VX_T(IY411,IRI,IRE,S,T)
         =L=
     (XKFX(IY411,IRE,IRI)
     +VXKNACCUMNET(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXKN(Y,IRE,IRI))
     )*X_RAMP*CHRONOHOUR(S,T)
;


QXRAMP2(IY411,IRE,IRI,S,T)$((1 GT CHRONOHOUR(S,T)*X_RAMP*0.5) AND (NOT (ORD(S) EQ 1 AND (ORD(T) EQ 1))) AND IS3(S) AND IXK_HASORPOT(IY411,IRE,IRI))..
-VX_T(IY411,IRE,IRI,S-1,T--1)$(ORD(T) EQ 1) - VX_T(IY411,IRE,IRI,S,T-1)$(NOT (ORD(T) EQ 1))
    + VX_T(IY411,IRE,IRI,S,T)

+VX_T(IY411,IRI,IRE,S-1,T--1)$(ORD(T) EQ 1) + VX_T(IY411,IRI,IRE,S,T-1)$(NOT (ORD(T) EQ 1))
    - VX_T(IY411,IRI,IRE,S,T)
         =L=
     (XKFX(IY411,IRE,IRI)
     +VXKNACCUMNET(IY411,IRE,IRI)$SUM(Y$(YVALUE(Y) LE YVALUE(IY411)),IXKN(Y,IRE,IRI))
     )*X_RAMP*CHRONOHOUR(S,T)
;

