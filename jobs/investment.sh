#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name --
#BSUB -J GREAT_investment
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 4GB of memory per core/slot --
#BSUB -R "rusage[mem=6GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 6GB
### -- set walltime limit: hh:mm --
#BSUB -W 24:00
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
#BSUB -o ../logs/GREAT_investment_%J.out
#BSUB -e ../logs/GREAT_investment_%J.err

# Load error handling and GAMS paths
source ../jobs/functions.sh

# Get run name
source config.sh

echo "Starting investment optimisation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_INV"

# Investment optimisation
cd model

# Run GAMS - if this fails, set -e will cause immediate exit via the trap
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --scenario_name="${run_name}_INV" $opts
gams_exit_code=$?

# Explicitly check GAMS exit code
if [ $gams_exit_code -ne 0 ]; then
    echo "ERROR: GAMS investment optimization failed with exit code $gams_exit_code"
    exit $gams_exit_code
fi

cd ..
optimality_check $LSB_JOBID 3
echo "Investment optimisation completed successfully at $(date)"

# Store simex files
if not [ -d "${PWD}/simex_INV" ]; then
    mkdir simex_INV
fi
/usr/bin/cp -rf simex/* simex_INV/

# Submit fullyear runs only if we reach this point
# bash jobs/submit_year_runs.sh
