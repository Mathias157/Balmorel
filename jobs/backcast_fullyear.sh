#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name --
#BSUB -J backcasting_fullyear
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 4GB of memory per core/slot --
#BSUB -R "rusage[mem=10GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 10GB
### -- set walltime limit: hh:mm --
#BSUB -W 72:00
### -- set the email address --
# please uncomment the following line and put in your e-mail address,
# if you want to receive e-mail notifications on a non-default address
##BSUB -u
### -- send notification at start --
##BSUB -B
### -- send notification at completion --
#BSUB -N
### -- Specify the output and error file. %J is the job-id --
### -- -o and -e mean append, -oo and -eo mean overwrite --
#BSUB -o ../logs/backcasting_fullyear_%J.out
#BSUB -e ../logs/backcasting_fullyear_%J.err

# Load error handling and GAMS paths
# source ../jobs/functions.sh

# Backcast year and seasons - change these. The year is written to data/Y.inc,
# so the model aborts if the inputs (e.g. TAX_CO2_ST) have no data for it.
# A seasons subset (e.g. 'S20') is a smoke test: no rolling run is submitted.
year=2023
seasons='S01*S52'

scenario='APS'
run_name='backcast'

# Check if simex exists, create if not
if not [ -d "simex" ]; then
  mkdir simex
fi

# Years and seasons in the simulation
printf 'SET Y(YYY) "Years in the simulation"\n/\n%s\n/;\n' "$year" >data/Y.inc
printf 'SET S(SSS) "Seasons in the simulation"\n/\n%s\n/;\n' "$seasons" >data/S.inc

# Full year simulation
cat data/T_full.inc >data/T.inc
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --SCNAME=$scenario --scenario_name="${run_name}_F${year}"
cd ../

optimality_check $LSB_JOBID 1

# Submit rolling horizon run (reads the year from data/Y.inc written above)
if [ "$seasons" = 'S01*S52' ]; then
  bsub <../jobs/backcast_rolling.sh
fi
