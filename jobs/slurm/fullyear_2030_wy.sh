#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2030_wy
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
#SBATCH --output=../logs/GREAT_fullyear_2030_wy_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2030_wy_%j.err

# Copy of fullyear_2050_wy.sh with only the year changed - edit that file and copy it over
# again, don't let the two drift apart.

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

year=2030
optfile=8 # barrier without crossover, see docs/adr/0035-fullyear-and-rolling-use-cplex-op8.md
require_optfile $optfile

echo "Starting weather year fullyear simulation at $(date)"
run_name="$(basename $PWD)"
# WY folder naming: <source_scenario>_WY<year> - see CONTEXT.md's "WY folder".
source_scenario="${run_name%_WY*}"
weather_year="${run_name##*_WY}"
echo "Run name: ${run_name}_F${year} (source scenario: ${source_scenario}, weather year: ${weather_year}, cplex.op${optfile})"

# Reuse the source scenario's already-completed investment decision instead
# of running our own - weather year runs never re-invest, see
# docs/adr/0013. A weather year folder never has its own simex_INV (there's
# no investment run to produce one), so this reads directly from the source
# scenario's, unlike the ordinary fullyear_2030.sh's `cp simex_INV/* simex/`.
/usr/bin/cp -rf "../${source_scenario}/simex_INV/"* simex/
/usr/bin/cp -f ../weatheryeardata/data_scaled/${weather_year}/*.inc data/

# Full year simulation - temporal resolution as usual, but the weather-
# driven VAR_T-style .inc files come from this weather year's scaled
# (long-term-corrected, aggregated) variant instead of whatever the source
# scenario's own base data would otherwise supply - see docs/adr/0014 and
# CONTEXT.md's "weatheryeardata".
cat ../base/data/Y_${year}.inc >data/Y.inc
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=${optfile} --scenario_name="${run_name}_F${year}" $opts
cd ..

# optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
sbatch ../jobs/slurm/rolling_${year}_wy.sh
