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
#BSUB -R "rusage[mem=6.5GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 6.5GB
### -- set walltime limit: hh:mm --
#BSUB -W 8:00
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
source ../jobs/functions.sh

scenario='APS'
run_name='backcast'

# Check if simex exists, create if not
if not [ -d "simex" ]; then
  mkdir simex
fi

# Full year simulation
cat data/T_full.inc >data/T.inc
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --SCNAME=$scenario --scenario_name="${run_name}_F2024"
cd ../

optimality_check $LSB_JOBID 1

# Submit rolling horizon run
bsub <../jobs/rolling_2024.sh
