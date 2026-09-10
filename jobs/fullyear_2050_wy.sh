#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name --
#BSUB -J GREAT_fullyear_2050
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 20GB of memory per core/slot --
#BSUB -R "rusage[mem=20GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 20GB
### -- set walltime limit: hh:mm --
### -- ALLN and VGN's fullyear solve is certain to exceed this: submit_year_runs.sh submits those
### -- two scenarios with `bsub -W 72:00` instead, which overrides this default. --
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
#BSUB -o ../logs/GREAT_fullyear_2050_%J.out
#BSUB -e ../logs/GREAT_fullyear_2050_%J.err

# Load error handling and GAMS paths
source ../jobs/functions.sh

# Get run name
source ./config.sh

echo "Starting weather year fullyear simulation at $(date)"
run_name="$(basename $PWD)"
# WY folder naming: <source_scenario>_WY<year> - see CONTEXT.md's "WY folder".
source_scenario="${run_name%_WY*}"
weather_year="${run_name##*_WY}"
echo "Run name: ${run_name}_F2050 (source scenario: ${source_scenario}, weather year: ${weather_year})"

# Reuse the source scenario's already-completed investment decision instead
# of running our own - weather year runs never re-invest, see
# docs/adr/0013. A weather year folder never has its own simex_INV (there's
# no investment run to produce one), so this reads directly from the source
# scenario's, unlike the ordinary fullyear_2050.sh's `cp simex_INV/* simex/`.
# /usr/bin/cp -rf "../${source_scenario}/simex_INV/"* simex/

# Full year simulation - temporal resolution as usual, but the weather-
# driven VAR_T-style .inc files come from this weather year's scaled
# (long-term-corrected, aggregated) variant instead of whatever the source
# scenario's own base data would otherwise supply - see docs/adr/0014 and
# CONTEXT.md's "weatheryeardata".
cat ../base/data/Y_full.inc >data/Y.inc
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc

cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --scenario_name="${run_name}_F2050" $opts
cd ..

# optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
bsub <../jobs/rolling_2050_wy.sh
