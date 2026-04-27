# Submit fullyear runs with sensitivity analysis on backup generation OMV
# (which, in turn, will submit rolling runs)

casenr=$1
year=$2
case_year="${casenr}_${year}"

case "${case_year}" in
"0_2030")
  echo """* Double
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =174.49;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =65.72;""" >>O2030/data/HYDROGEN_GDATA.inc
  ;;
"1_2030")
  echo """* 500 €/MWh
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =325.51;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =434.28;""" >>O2030/data/HYDROGEN_GDATA.inc
  ;;
"2_2030")
  echo """* 3000 €/MWh
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =2825.51;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =2934.28;""" >>O2030/data/HYDROGEN_GDATA.inc
  ;;
"0_2040")
  echo """* Double
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =201.49;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =75.32;""" >>O2040/data/HYDROGEN_GDATA.inc
  ;;
"1_2040")
  echo """* 500 €/MWh
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =298.51;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =424.68;""" >>O2040/data/HYDROGEN_GDATA.inc
  ;;
"2_2040")
  echo """* 3000 €/MWh
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =2798.51;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =2924.68;""" >>O2040/data/HYDROGEN_GDATA.inc
  ;;
"0_2050")
  echo """* Double
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =218.89;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =81.52;""" >>O2050/data/HYDROGEN_GDATA.inc
  ;;
"1_2050")
  echo """* 500 €/MWh
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =281.11;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =418.48;""" >>O2050/data/HYDROGEN_GDATA.inc
  ;;
"2_2050")
  echo """* 3000 €/MWh
GDATA('GNR_BACKUP_ELECTRICITY','GDOMVCOST0')            =2781.11;
GDATA('GNR_BACKUP_HEAT','GDOMVCOST0')                   =2918.48;""" >>O2050/data/HYDROGEN_GDATA.inc
  ;;
*)
  echo "Usage: $0 {0|1|2}"
  exit 1
  ;;
esac

case $casenr in
0)
  echo """GDATA('GNR_BACKUP_HYDROGEN','GDOMVCOST0')               =20;
GDATA('GNR_BACKUP_BIOMETHANE','GDOMVCOST0')             =20;
GDATA('GNR_BACKUP_ELECTRICITY_CT-BIOMETH','GDOMVCOST0') =8.82;
""" >>"O${year}/data/HYDROGEN_GDATA.inc"
  ;;
1)
  echo """GDATA('GNR_BACKUP_HYDROGEN','GDOMVCOST0')               =500;
GDATA('GNR_BACKUP_BIOMETHANE','GDOMVCOST0')             =500;
GDATA('GNR_BACKUP_ELECTRICITY_CT-BIOMETH','GDOMVCOST0') =500;
""" >>"O${year}/data/HYDROGEN_GDATA.inc"
  ;;
2)
  echo """GDATA('GNR_BACKUP_HYDROGEN','GDOMVCOST0')               =2990;
GDATA('GNR_BACKUP_BIOMETHANE','GDOMVCOST0')             =2990;
GDATA('GNR_BACKUP_ELECTRICITY_CT-BIOMETH','GDOMVCOST0') =2995.59;
""" >>"O${year}/data/HYDROGEN_GDATA.inc"
  ;;
*)
  echo "No $0 case - available cases: 0, 1 or 2"
  exit 1
  ;;
esac

bsub <jobs/fullyear_${year}.sh
