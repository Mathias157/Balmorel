#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=GREAT_rolling_2050
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=4-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_rolling_2050_%j.out
#SBATCH --error=../logs/GREAT_rolling_2050_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

echo "Starting rolling seasons simulation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_R2050"

# RESLIM below the job's own wall-time (see #SBATCH --time above), so CPLEX stops itself and GAMS
# can still write its savepoint/logs before the scheduler kills the job outright. Margin is a
# conservative starting guess - tune once real run timings are known.
# See docs/adr/0001-warm-start-fullyear-timeout.md and docs/adr/0002-slurm-migration.md.
reslim_seconds=$((2 * 24 * 3600 - 45 * 60))

# Rolling horison simulation
cat ../base/data/Y_roll.inc >data/Y.inc
cat ../base/data/T_roll.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_roll.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=2 --RESLIM=${reslim_seconds} --scenario_name="${run_name}_R2050" $opts
cd ..

optimality_check $SLURM_JOB_ID 52

if [ -f ../jobs/userfunctions.sh ]; then
    . ../jobs/userfunctions.sh
    verifications $run_name
fi
