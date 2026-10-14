extra_arg=$1

for scenario in "base" \
    "FENHPN" \
    "HPNH2N" \
    "H2NELN" \
    "ELNDCN" \
    "H2NNPY" \
    "EINELN" \
    "EVNSSN" \
    "EVNH2N" \
    "EVN" \
    "TPNH2N" \
    "FENEIN" \
    "H2NDCN" \
    "FENSSN" \
    "FENH2N" \
    "H2NSSN" \
    "EINDCN" \
    "PVNDCN" \
    "PVNNPY" \
    "PVNH2N" \
    "EVNFEN" \
    "SSN" \
    "PVNHPN" \
    "EINNPY" \
    "FEN" \
    "PVNSSN" \
    "PVNELN" \
    "EIN" \
    "EINHSN" \
    "HPNDCN" \
    "EVNEIN" \
    "TPNDCN" \
    "TPNSSN" \
    "ELN" \
    "EVNDCN" \
    "EINTPN" \
    "NPYDCN" \
    "HPNEIN" \
    "PVNFEN" \
    "HPNHSN" \
    "SSNDCN" \
    "ELNSSN" \
    "HSNDCN" \
    "NPYHSN" \
    "HPNTPN" \
    "HPNSSN" \
    "EVNNPY" \
    "HPN" \
    "FENTPN" \
    "TPNNPY" \
    "PVNEIN" \
    "NPY" \
    "FENNPY" \
    "TPNELN" \
    "PVN" \
    "PVNHSN" \
    "PVNTPN" \
    "TPN" \
    "H2NHSN" \
    "PVNEVN" \
    "TPNHSN" \
    "EVNELN" \
    "EVNHPN" \
    "EVNTPN" \
    "FENDCN" \
    "EINH2N" \
    "FENELN" \
    "HPNNPY" \
    "H2N" \
    "EINSSN" \
    "DCN" \
    "EVNHSN" \
    "ELNNPY" \
    "ELNHSN" \
    "FENHSN" \
    "HSN" \
    "HSNSSN" \
    "HPNELN" \
    "NPYSSN" \
    "ALLN"; do
    pixi run sophia-sync-mainresults "$scenario" -- --exclude *R2030.gdx
done

pixi run analyse $extra_arg --filters 'Scenario in ["base_INV","FENHPN_INV" ,"HPNH2N_INV" ,"H2NELN_INV" ,"ELNDCN_INV" ,"H2NNPY_INV" ,"EINELN_INV" ,"EVNSSN_INV" ,"EVNH2N_INV" ,"EVN_INV" ,"TPNH2N_INV" ,"FENEIN_INV" ,"H2NDCN_INV" ,"FENSSN_INV" ,"FENH2N_INV" ,"H2NSSN_INV" ,"EINDCN_INV" ,"PVNDCN_INV" ,"PVNNPY_INV" ,"PVNH2N_INV" ,"EVNFEN_INV" ,"SSN_INV" ,"PVNHPN_INV" ,"EINNPY_INV" ,"FEN_INV" ,"PVNSSN_INV" ,"PVNELN_INV" ,"EIN_INV" ,"EINHSN_INV" ,"HPNDCN_INV" ,"EVNEIN_INV" ,"TPNDCN_INV" ,"TPNSSN_INV" ,"ELN_INV" ,"EVNDCN_INV" ,"EINTPN_INV" ,"NPYDCN_INV" ,"HPNEIN_INV" ,"PVNFEN_INV" ,"HPNHSN_INV" ,"SSNDCN_INV" ,"ELNSSN_INV" ,"HSNDCN_INV" ,"NPYHSN_INV" ,"HPNTPN_INV" ,"HPNSSN_INV" ,"EVNNPY_INV" ,"HPN_INV" ,"FENTPN_INV" ,"TPNNPY_INV" ,"PVNEIN_INV" ,"NPY_INV" ,"FENNPY_INV" ,"TPNELN_INV" ,"PVN_INV" ,"PVNHSN_INV" ,"PVNTPN_INV" ,"TPN_INV" ,"H2NHSN_INV" ,"PVNEVN_INV" ,"TPNHSN_INV" ,"EVNELN_INV" ,"EVNHPN_INV" ,"EVNTPN_INV" ,"FENDCN_INV" ,"EINH2N_INV" ,"FENELN_INV" ,"HPNNPY_INV" ,"H2N_INV" ,"EINSSN_INV" ,"DCN_INV" ,"EVNHSN_INV" ,"ELNNPY_INV" ,"ELNHSN_INV" ,"FENHSN_INV" ,"HSN_INV" ,"HSNSSN_INV" ,"HPNELN_INV" ,"NPYSSN_INV" ,"ALLN_INV"] and Commodity =="ELECTRICITY" and Year == "2050"' production
pixi run analyse $extra_arg --filters 'Scenario in ["base_INV","FENHPN_INV" ,"HPNH2N_INV" ,"H2NELN_INV" ,"ELNDCN_INV" ,"H2NNPY_INV" ,"EINELN_INV" ,"EVNSSN_INV" ,"EVNH2N_INV" ,"EVN_INV" ,"TPNH2N_INV" ,"FENEIN_INV" ,"H2NDCN_INV" ,"FENSSN_INV" ,"FENH2N_INV" ,"H2NSSN_INV" ,"EINDCN_INV" ,"PVNDCN_INV" ,"PVNNPY_INV" ,"PVNH2N_INV" ,"EVNFEN_INV" ,"SSN_INV" ,"PVNHPN_INV" ,"EINNPY_INV" ,"FEN_INV" ,"PVNSSN_INV" ,"PVNELN_INV" ,"EIN_INV" ,"EINHSN_INV" ,"HPNDCN_INV" ,"EVNEIN_INV" ,"TPNDCN_INV" ,"TPNSSN_INV" ,"ELN_INV" ,"EVNDCN_INV" ,"EINTPN_INV" ,"NPYDCN_INV" ,"HPNEIN_INV" ,"PVNFEN_INV" ,"HPNHSN_INV" ,"SSNDCN_INV" ,"ELNSSN_INV" ,"HSNDCN_INV" ,"NPYHSN_INV" ,"HPNTPN_INV" ,"HPNSSN_INV" ,"EVNNPY_INV" ,"HPN_INV" ,"FENTPN_INV" ,"TPNNPY_INV" ,"PVNEIN_INV" ,"NPY_INV" ,"FENNPY_INV" ,"TPNELN_INV" ,"PVN_INV" ,"PVNHSN_INV" ,"PVNTPN_INV" ,"TPN_INV" ,"H2NHSN_INV" ,"PVNEVN_INV" ,"TPNHSN_INV" ,"EVNELN_INV" ,"EVNHPN_INV" ,"EVNTPN_INV" ,"FENDCN_INV" ,"EINH2N_INV" ,"FENELN_INV" ,"HPNNPY_INV" ,"H2N_INV" ,"EINSSN_INV" ,"DCN_INV" ,"EVNHSN_INV" ,"ELNNPY_INV" ,"ELNHSN_INV" ,"FENHSN_INV" ,"HSN_INV" ,"HSNSSN_INV" ,"HPNELN_INV" ,"NPYSSN_INV" ,"ALLN_INV"] and Year == "2050"' costs

# weather_year=1982
# for i in {0..39}; do
#     pixi run sophia-sync-mainresults "base_WY${weather_year}" -- --exclude "*R2050.gdx"
#     ((weather_year = $weather_year + 1))
# done
