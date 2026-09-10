#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name --
#BSUB -J GREAT_rolling_2050
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 11GB of memory per core/slot --
#BSUB -R "rusage[mem=20GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 20GB
### -- set walltime limit: hh:mm --
### -- ALLN and VGN's rolling solve is certain to exceed this: submit_year_runs.sh submits those
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
#BSUB -o ../logs/GREAT_rolling_2050_%J.out
#BSUB -e ../logs/GREAT_rolling_2050_%J.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

echo "Starting weather year rolling seasons simulation at $(date)"
run_name="$(basename $PWD)"
# WY folder naming: <source_scenario>_WY<year> - see CONTEXT.md's "WY folder".
source_scenario="${run_name%_WY*}"
weather_year="${run_name##*_WY}"
echo "Run name: ${run_name}_R2050 (source scenario: ${source_scenario}, weather year: ${weather_year})"

# RESLIM below the job's own wall-time (see #SBATCH --time above), so CPLEX stops itself and GAMS
# can still write its savepoint/logs before the scheduler kills the job outright.
# See docs/adr/0001-warm-start-fullyear-timeout.md and docs/adr/0002-slurm-migration.md.
reslim_seconds=$((2 * 24 * 3600 - 45 * 60))

# Rolling horizon simulation - this weather year's raw (8760h resolution)
# variant, not whatever the source scenario's own base data would otherwise
# supply - see docs/adr/0014 and CONTEXT.md's "weatheryeardata".
/usr/bin/cp -f ../weatheryeardata/data_raw/${weather_year}/*.inc data/
cat ../base/data/Y_roll.inc >data/Y.inc
cat ../base/data/T_roll.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc

cd model
cat balopt_roll.opt >balopt.opt
gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --RESLIM=${reslim_seconds} --scenario_name="${run_name}_R2050" $opts
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
