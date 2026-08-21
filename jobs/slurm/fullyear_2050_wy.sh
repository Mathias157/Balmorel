#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windq
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2050_wy
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=6-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_fullyear_2050_wy_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2050_wy_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

echo "Starting weather year fullyear simulation at $(date)"
run_name="$(basename $PWD)"
# WY folder naming: <source_scenario>_WY<year> - see CONTEXT.md's "WY folder".
source_scenario="${run_name%_WY*}"
weather_year="${run_name##*_WY}"
echo "Run name: ${run_name}_F2050 (source scenario: ${source_scenario}, weather year: ${weather_year})"

# Reuse the source scenario's already-completed investment decision instead
# of running our own - weather year runs never re-invest, see
# docs/adr/0013. A weather year folder never has its own simex_INV (there's
# no investment run to produce one), so this reads directly from the source
# scenario's, unlike the ordinary fullyear_2050.sh's `cp simex_INV/* simex/`.
/usr/bin/cp -rf "../${source_scenario}/simex_INV/"* simex/

# Full year simulation - temporal resolution as usual, but the weather-
# driven VAR_T-style .inc files come from this weather year's scaled
# (long-term-corrected, aggregated) variant instead of whatever the source
# scenario's own base data would otherwise supply - see docs/adr/0014 and
# CONTEXT.md's "weatheryeardata".
cat ../base/data/Y_full.inc >data/Y.inc
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cp -f ../weatheryeardata/data_scaled/${weather_year}/*.inc data/
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=2 --scenario_name="${run_name}_F2050" $opts
cd ..

# optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
sbatch ../jobs/slurm/rolling_2050_wy.sh
