#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windq
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2040
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-08:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_fullyear_2040_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2040_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

echo "Starting fullyear simulation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_F2040"

# Copy simex files from investment run
/usr/bin/cp -rf simex_INV/* simex/

# Full year simulation
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=2 --scenario_name="${run_name}_F2040" $opts
cd ..

optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
sbatch ../jobs/slurm/rolling_2040.sh
