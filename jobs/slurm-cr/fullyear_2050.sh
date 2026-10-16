#!/bin/sh
### General options
### -- specify partition and account --
#SBATCH --partition=fatnode
#SBATCH --account=dtu_00075
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2050
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- memory: CR_CORE does not reserve it, only picks nodes with this much in total --
#SBATCH --mem=100G
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=2-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_fullyear_2050_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2050_%j.err

# Computerome copy of jobs/slurm/fullyear_2050.sh. fullyear_2030.sh/fullyear_2040.sh are generated
# copies of this file with only the year (and walltime) changed - keep them that way.
# Runs either in a scenario folder or in one of its Year copies, see functions.sh.

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm-cr/functions.sh

# Get run name
source ./config.sh

year=2050
optfile=8 # barrier without crossover, see docs/adr/0035-fullyear-and-rolling-use-cplex-op8.md
require_optfile $optfile

echo "Starting fullyear simulation at $(date)"
# A Year copy names its results after its source scenario
run_name="${source_scenario:-$(basename $PWD)}"
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

# Don't spend days of rolling on a non-optimal fullyear's storage levels
optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
sbatch ../jobs/slurm-cr/rolling_${year}.sh
