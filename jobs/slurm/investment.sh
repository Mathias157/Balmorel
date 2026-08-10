#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windq
### -- set the job Name --
#SBATCH --job-name=GREAT_investment
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=1-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_investment_%j.out
#SBATCH --error=../logs/GREAT_investment_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

echo "Starting investment optimisation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_INV"

# Append H2 investments if scenario != ELN
if [[ "${run_name}" != "ELN" ]]; then
    opts="${opts} --H2TransInvest yes"
fi

# Temporal resolution
cat ../base/data/Y_inv.inc >data/Y.inc
cat ../base/data/T_inv.inc >data/T.inc
cat ../base/data/S_inv.inc >data/S.inc

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
if [ ! -d "${PWD}/simex_INV" ]; then
    mkdir simex_INV
fi
/usr/bin/cp -rf simex/* simex_INV/

# Submit fullyear run only if we reach this point
sbatch ../jobs/slurm/fullyear_2050.sh
