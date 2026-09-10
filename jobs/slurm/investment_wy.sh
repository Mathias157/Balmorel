#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=GREAT_investment
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-10:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_investment_%j.out
#SBATCH --error=../logs/GREAT_investment_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
# source config.sh

echo "$opts"

echo "Starting weather year investment optimisation at $(date)"
run_name="$(basename $PWD)"
# WY folder naming: <source_scenario>_WY<year> - see CONTEXT.md's "WY folder".
source_scenario="${run_name%_WY*}"
weather_year="${run_name##*_WY}"
echo "Run name: ${run_name}_INV (source scenario: ${source_scenario}, weather year: ${weather_year})"

# Append H2 investments if scenario != ELN
if [[ "${run_name}" != "ELN" && "${run_name}" != "ALLN" ]]; then
    opts="${opts} --H2TransInvest yes"
fi

# Temporal resolution
cat ../base/data/Y_inv.inc >data/Y.inc
cat ../base/data/T_inv.inc >data/T.inc
cat ../base/data/S_inv.inc >data/S.inc
/usr/bin/cp -f ../weatheryeardata/data_scaled/${weather_year}/*.inc data/

# Investment optimisation
cd model
cat balopt_inv.opt >balopt.opt

# Run GAMS - if this fails, set -e will cause immediate exit via the trap
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=2 --scenario_name="${run_name}_INV" $opts
gams_exit_code=$?

# Explicitly check GAMS exit code
if [ $gams_exit_code -ne 0 ]; then
    echo "ERROR: GAMS investment optimization failed with exit code $gams_exit_code"
    exit $gams_exit_code
fi

cd ..
optimality_check $SLURM_JOB_ID 3
echo "Investment optimisation completed successfully at $(date)"

# Store simex files
if not [ -d "${PWD}/simex_INV" ]; then
    mkdir simex_INV
fi
/usr/bin/cp -rf simex/* simex_INV/

# Submit fullyear runs only if we reach this point
sbatch ../jobs/slurm/fullyear_2050_wy.sh
