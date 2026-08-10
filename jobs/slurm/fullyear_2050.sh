#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windq
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2050
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=2-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_fullyear_2050_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2050_%j.err

# SLURM does not guarantee the job starts in the submission directory on this cluster - force it
# explicitly, since everything below assumes cwd == the directory sbatch was run from.
cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
source ../jobs/slurm/functions.sh

# Get run name
source ./config.sh

echo "Starting fullyear simulation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_F2050"

# ALLN and VGN's fullyear LP is certain to be the longest-running solve in the pipeline. For these
# two scenarios only, use dual simplex (cplex.op3) instead of barrier so a timed-out attempt's
# savepoint can genuinely warm-start the next one, and detect a graceful RESLIM stop so the
# pipeline resubmits instead of hard-failing. Every other scenario behaves exactly as before.
# See docs/adr/0001-warm-start-fullyear-timeout.md and docs/adr/0002-slurm-migration.md.
WARMSTART_HOP="${WARMSTART_HOP:-0}"
MAX_WARMSTART_HOPS=3
if [[ "$run_name" == "ALLN" || "$run_name" == "VGN" ]]; then
    warmstart_enabled=yes
else
    warmstart_enabled=no
fi

# Copy simex files from investment run
/usr/bin/cp -rf simex_INV/* simex/

# Full year simulation
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_full.opt >balopt.opt
if [[ "$warmstart_enabled" == "yes" ]]; then
    # 2-day wall-time (see #SBATCH --time above) minus a conservative margin for data read/write.
    reslim_seconds=$((2 * 24 * 3600 - 45 * 60))
    warmstart_args=""
    if [[ "$WARMSTART_HOP" -gt 0 ]]; then
        warmstart_args="--WARMSTART=yes --WARMSTARTGDX=${WARMSTART_GDX}"
        echo "Warm-starting from ${WARMSTART_GDX} (hop ${WARMSTART_HOP}/${MAX_WARMSTART_HOPS})"
    fi
    gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=3 --RESLIM=${reslim_seconds} ${warmstart_args} --scenario_name="${run_name}_F2050" $opts
else
    gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=2 --scenario_name="${run_name}_F2050" $opts
fi
cd ..

# If CPLEX hit RESLIM rather than finding an optimum, resubmit a warm-started continuation instead
# of hard-failing (capped at MAX_WARMSTART_HOPS so a scenario that never converges doesn't chain
# forever). Any other failure (infeasibility, GAMS error, etc.) falls through to optimality_check
# below and hard-stops the pipeline exactly as it does today.
if [[ "$warmstart_enabled" == "yes" ]] && rg -q 'Resource limit reached' logerror/logfile.out; then
    if [[ "$WARMSTART_HOP" -lt "$MAX_WARMSTART_HOPS" ]]; then
        next_hop=$((WARMSTART_HOP + 1))
        warmstart_gdx="$(pwd)/simex/warmstart_hop${WARMSTART_HOP}.gdx"
        cp model/BALBASE4_p.gdx "$warmstart_gdx"
        echo "TIMEOUT: fullyear solve for ${run_name} hit RESLIM without reaching optimality."
        echo "Resubmitting warm-started hop ${next_hop}/${MAX_WARMSTART_HOPS} from ${warmstart_gdx}."
        sbatch --export=ALL,WARMSTART_HOP=${next_hop},WARMSTART_GDX=${warmstart_gdx} ../jobs/slurm/fullyear_2050.sh
        exit 0
    else
        echo "ERROR: fullyear solve for ${run_name} still hasn't reached optimality after ${MAX_WARMSTART_HOPS} warm-started hops."
        exit 1
    fi
fi

# optimality_check $SLURM_JOB_ID 1

# Submit rolling horizon run
sbatch ../jobs/slurm/rolling_2050.sh
