#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2040
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=1-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_fullyear_2040_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2040_%j.err

# Copy of fullyear_2050.sh with only the year changed - edit that file and copy it over again,
# don't let the two drift apart.

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

year=2040
optfile=8 # barrier without crossover, see docs/adr/0035-fullyear-and-rolling-use-cplex-op8.md
require_optfile $optfile

echo "Starting fullyear simulation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_F${year} (cplex.op${optfile})"

# Copy simex files from investment run
/usr/bin/cp -rf simex_INV/* simex/

# Full year simulation
cat ../base/data/Y_${year}.inc >data/Y.inc
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=${optfile} --scenario_name="${run_name}_F${year}" $opts
cd ..

# optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
sbatch ../jobs/slurm/rolling_${year}.sh
