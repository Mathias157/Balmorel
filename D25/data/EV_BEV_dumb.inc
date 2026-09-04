* Fleet-split EV dumb-charging (D25): dumb charging is handled exogenously
* (DE_EV_DUMB.inc), so the addon's own smart-only fleet has EV_BEV_dumb=0 - no
* forced VEV_G2V_BEV.LO floor, no infeasibility risk without V2G.
EV_BEV_dumb(YYY,RRR)=0;
