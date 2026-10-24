#!/bin/sh
### General options
### -- specify partition and account --
#SBATCH --partition=fatnode
#SBATCH --account=dtu_00075
### -- set the job Name --
#SBATCH --job-name=GREAT_rolling_2040
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- memory: CR_CORE does not reserve it, only picks nodes with this much in total --
#SBATCH --mem=100G
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=2-12:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_rolling_2040_%j.out
#SBATCH --error=../logs/GREAT_rolling_2040_%j.err

# Copy of rolling_2050.sh with only the year changed - edit that file and copy it over again,
# don't let the two drift apart.
# Runs either in a scenario folder or in one of its Year copies, see functions.sh. Never chains to
# the next target year: fan_out_target_years already started all of them.

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm-cr/functions.sh

# Get run name
source ./config.sh

year=2040
optfile=8 # barrier without crossover, see docs/adr/0035-fullyear-and-rolling-use-cplex-op8.md
require_optfile $optfile

echo "Starting rolling seasons simulation at $(date)"
# A Year copy names its results after its source scenario
run_name="${source_scenario:-$(basename $PWD)}"
echo "Run name: ${run_name}_R${year} (cplex.op${optfile})"

# Rolling horison simulation
cat ../base/data/Y_${year}.inc >data/Y.inc
cat ../base/data/T_roll.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_roll.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=${optfile} --scenario_name="${run_name}_R${year}" $opts
cd ..

optimality_check $SLURM_JOB_ID 52
penalty_check $SLURM_JOB_ID
ccs_storage_check "${run_name}_R${year}"

if [ -f ../jobs/userfunctions.sh ]; then
    . ../jobs/userfunctions.sh
    verifications $run_name
fi

# Year copy only: move results to the source scenario and delete the copy
return_year_copy $year
