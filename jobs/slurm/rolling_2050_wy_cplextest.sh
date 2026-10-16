#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=GREAT_rolling_2050_cplextest
### -- ask for number of cpus (default: 1) - submit_cplex_test.sh overrides this on the sbatch line --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=4-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_rolling_2050_cplextest_%j.out
#SBATCH --error=../logs/GREAT_rolling_2050_cplextest_%j.err

# CPLEX option file test: the same rolling 2050 weather year run as rolling_2050_wy.sh, but with a
# different --USEOPTIONFILE, in a scratch copy of an already-completed WY folder. Submit only via
# jobs/slurm/submit_cplex_test.sh, which creates that copy and passes WEATHER_YEAR, OPTFILE and
# SCENARIO_NAME explicitly - nothing here is parsed from the folder name.
#
# Differences to rolling_2050_wy.sh, all deliberate:
# - no optimality_check exit: a status-5 solve is exactly what the comparison needs to see, so the
#   job always runs all 52 seasons and ends with solve_timings.sh's per-status count instead;
# - GAMS profiling (profile=1, statements >= 60 s written to gams_profile.txt) to locate the ~17 h of
#   non-solver GAMS time per rolling run. Does not affect the solver, so timings stay comparable.

cd "$SLURM_SUBMIT_DIR"

source ../jobs/slurm/functions.sh
source ./config.sh

: "${WEATHER_YEAR:?set by submit_cplex_test.sh}"
: "${OPTFILE:?set by submit_cplex_test.sh}"
: "${SCENARIO_NAME:?set by submit_cplex_test.sh}"

echo "Starting CPLEX test rolling seasons simulation at $(date)"
echo "Run name: ${SCENARIO_NAME} (weather year: ${WEATHER_YEAR}, cplex.op${OPTFILE}, ${SLURM_CPUS_PER_TASK} threads)"

# Identical input staging to rolling_2050_wy.sh.
/usr/bin/cp -f ../weatheryeardata/data_raw/${WEATHER_YEAR}/*.inc data/

cat ../base/data/Y_2050.inc >data/Y.inc
cat ../base/data/T_roll.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_roll.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=${OPTFILE} --scenario_name="${SCENARIO_NAME}" \
    profile=1 profileTol=60 profileFile=gams_profile.txt $opts
cd ..

../jobs/slurm/solve_timings.sh ../logs/GREAT_rolling_2050_cplextest_${SLURM_JOB_ID}.out

# Same disk-freeing as rolling_2050_wy.sh - the log and gams_profile.txt hold everything the
# comparison needs.
rm -f model/Balmorel.lst
