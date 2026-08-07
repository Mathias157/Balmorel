extra_arg=$1

for scenario in "EVN" "HPN" "TPN" "ELN" "HSNSSN" "HSN" "SSN" "EIN" "DCN" "H2N" "base"; do
    pixi run sync-mainresults "$scenario"
done

pixi run analyse $extra_arg --filters 'Scenario in ["EVN_R2050" , "HPN_R2050" , "TPN_R2050" , "ELN_R2050" , "HSNSSN_R2050" , "HSN_R2050" , "SSN_R2050" , "EIN_R2050" , "DCN_R2050" , "H2N_R2050" , "base_R2050"] and Commodity =="ELECTRICITY" and Year == "2050"' production
