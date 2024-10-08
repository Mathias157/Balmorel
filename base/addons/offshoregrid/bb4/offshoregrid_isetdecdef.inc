*Offshore grid add-on. Implemented by Juan Gea Bermudez 2019

SET IGKN_ES(GGG)         "Technologies lines whose cost depends on economy of scale";
SET IXKN_ES(IRRRE,IRRRI) "Transmission lines whose cost depends on economy of scale";
SET IGHUB(G)           "Hub technologies";


IGKN_ES(GGG)$SUM(XES,GKN_ES(GGG,XES))=YES;
IXKN_ES(IRRRE,IRRRI)$SUM(XES,XKN_ES(IRRRE,IRRRI,XES))=YES;

$ifi not %TechInvest%==yes   IGKN_ES(GGG)=NO;
$ifi not %TransInvest%==yes  IXKN_ES(IRRRE,IRRRI)=NO;

$ifi not %OFFSHOREGRID_ES_GEN%==yes  IGKN_ES(GGG)=NO;
$ifi not %OFFSHOREGRID_ES_ELTRANS%==yes  IXKN_ES(IRRRE,IRRRI)=NO;

IGHUB(G)= YES$(GDATA(G,'GDTYPE') EQ HUB_OFF);


