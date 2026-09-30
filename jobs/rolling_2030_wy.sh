#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name --
#BSUB -J GREAT_rolling_2030
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 11GB of memory per core/slot --
#BSUB -R "rusage[mem=20GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 20GB
### -- set walltime limit: hh:mm --
#BSUB -W 48:00
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
#BSUB -o ../logs/GREAT_rolling_2030_%J.out
#BSUB -e ../logs/GREAT_rolling_2030_%J.err

# Copy of rolling_2050_wy.sh with only the year changed - edit that file and copy it over
# again, don't let the two drift apart.

# Load error handling and GAMS paths
source ../jobs/functions.sh

# Get run name
source ./config.sh

year=2030
optfile=8 # barrier without crossover, see docs/adr/0035-fullyear-and-rolling-use-cplex-op8.md
require_optfile $optfile

echo "Starting weather year rolling seasons simulation at $(date)"
run_name="$(basename $PWD)"
# WY folder naming: <source_scenario>_WY<year> - see CONTEXT.md's "WY folder".
source_scenario="${run_name%_WY*}"
weather_year="${run_name##*_WY}"
echo "Run name: ${run_name}_R${year} (source scenario: ${source_scenario}, weather year: ${weather_year}, cplex.op${optfile})"

# Rolling horizon simulation - this weather year's raw (8760h resolution)
# variant, not whatever the source scenario's own base data would otherwise
# supply - see docs/adr/0014 and CONTEXT.md's "weatheryeardata".
/usr/bin/cp -f ../weatheryeardata/data_raw/${weather_year}/*.inc data/
cat ../base/data/Y_${year}.inc >data/Y.inc
cat ../base/data/T_roll.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc

cd model
cat balopt_roll.opt >balopt.opt
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=${optfile} --scenario_name="${run_name}_R${year}" $opts
cd ..

optimality_check $LSB_JOBID 52

# Free disk: Balmorel.lst regularly runs 100MB+ per solve, is never read
# back by anything downstream, and model/ is shared with the fullyear step
# above (so this is the one point per weather year run where it's safe to
# remove - see docs/adr/0014). Only reached on a successful (optimal) solve
# - optimality_check above exits the script first on failure, deliberately
# leaving Balmorel.lst in place to debug from.
rm -f model/Balmorel.lst

if [ -f ../jobs/userfunctions.sh ]; then
    . ../jobs/userfunctions.sh
    verifications $run_name
fi
