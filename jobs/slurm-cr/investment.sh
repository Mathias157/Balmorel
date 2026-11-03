#!/bin/sh
### General options
### -- specify partition and account --
#SBATCH --partition=fatnode
#SBATCH --account=dtu_00075
### -- set the job Name --
#SBATCH --job-name=GREAT_investment
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- memory: CR_CORE does not reserve it, only picks nodes with this much in total --
#SBATCH --mem=100G
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-16:00:00
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
source ../jobs/slurm-cr/functions.sh

# Get run name
source ./config.sh

# Barrier with crossover, see docs/adr/0080-investment-runs-return-to-cplex-op2.md. For a run that
# stalled in the clean-up after crossover, submit with INV_OPTFILE (e.g. 9: op2 without scaind 1)
# and/or LASTYEAR_OPTFILE (e.g. 8: no crossover in 2050, the last year), GREAT docs/adr/0095
optfile=${INV_OPTFILE:-2}
require_optfile $optfile
lastyear_opts=""
if [ -n "${LASTYEAR_OPTFILE:-}" ]; then
    require_optfile $LASTYEAR_OPTFILE
    lastyear_opts="--LASTYEAR_OPTFILE=${LASTYEAR_OPTFILE}"
fi

echo "Starting investment optimisation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_INV (cplex.op${optfile}${LASTYEAR_OPTFILE:+, last year cplex.op${LASTYEAR_OPTFILE}})"

# Temporal resolution
cat ../base/data/Y_inv.inc >data/Y.inc
cat ../base/data/T_inv.inc >data/T.inc
cat ../base/data/S_inv.inc >data/S.inc

# Investment optimisation
cd model
cat balopt_inv.opt >balopt.opt

# Run GAMS - if this fails, set -e will cause immediate exit via the trap
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=${optfile} --scenario_name="${run_name}_INV" $opts $lastyear_opts
gams_exit_code=$?

# Explicitly check GAMS exit code
if [ $gams_exit_code -ne 0 ]; then
    echo "ERROR: GAMS investment optimization failed with exit code $gams_exit_code"
    exit $gams_exit_code
fi

cd ..
# A no-crossover last year has no crossover to repair a stalled barrier, and its capacities seed every
# fullyear and rolling run, so it gets fullyear's strict check (docs/adr/0090, 0094)
optimality_check $SLURM_JOB_ID 3 ${LASTYEAR_OPTFILE:+strict}
penalty_check $SLURM_JOB_ID
echo "Investment optimisation completed successfully at $(date)"

# Store simex files
if [ ! -d "${PWD}/simex_INV" ]; then
    mkdir simex_INV
fi
/usr/bin/cp -rf simex/* simex_INV/

# Start all target years at once (2040/2050 in Year copies) only if we reach this point
fan_out_target_years
