#!/bin/sh
### General options
### -- specify queue --
#BSUB -q hpc
### -- set the job Name --
#BSUB -J GREAT_fullyear_2050
### -- ask for number of cores (default: 1) --
#BSUB -n 10
### -- specify that the cores must be on the same host --
#BSUB -R "span[hosts=1]"
### -- specify that we need 11GB of memory per core/slot --
#BSUB -R "rusage[mem=11GB]"
### -- specify that we want the job to get killed if it exceeds 5 GB per core/slot --
#BSUB -M 11GB
### -- set walltime limit: hh:mm --
### -- ALLN and VGN's fullyear solve is certain to exceed this: submit_year_runs.sh submits those
### -- two scenarios with `bsub -W 72:00` instead, which overrides this default. --
#BSUB -W 72:00
### -- set the email address --
# please uncomment the following line and put in your e-mail address,
# if you want to receive e-mail notifications on a non-default address
##BSUB -u
### -- send notification at start --
##BSUB -B
### -- send notification at completion --
#BSUB -N
### -- Specify the output and error file. %J is the job-id --
### -- -o and -e mean append, -oo and -eo mean overwrite --
#BSUB -o ../logs/GREAT_fullyear_2050_%J.out
#BSUB -e ../logs/GREAT_fullyear_2050_%J.err

# Load error handling and GAMS paths
source ../jobs/functions.sh

# Get scenario choice and run name from jobs/scenario_choice.sh
source config.sh

echo "Starting fullyear simulation at $(date)"
run_name="$(basename $PWD)"
echo "Run name: ${run_name}_F2050"

# ALLN and VGN's fullyear LP is certain to run past a single 72h job. For these two scenarios only,
# use dual simplex (cplex.op3) instead of barrier so a timed-out attempt's savepoint can genuinely
# warm-start the next one, and detect a graceful RESLIM stop so the pipeline resubmits instead of
# hard-failing. Every other scenario behaves exactly as before.
# See docs/adr/0001-warm-start-fullyear-timeout.md.
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
  # 72h wall-time (see submit_year_runs.sh) minus a conservative margin for data read/write.
  reslim_seconds=$((72 * 3600 - 45 * 60))
  warmstart_args=""
  if [[ "$WARMSTART_HOP" -gt 0 ]]; then
    warmstart_args="--WARMSTART=yes --WARMSTARTGDX=${WARMSTART_GDX}"
    echo "Warm-starting from ${WARMSTART_GDX} (hop ${WARMSTART_HOP}/${MAX_WARMSTART_HOPS})"
  fi
  gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=3 --RESLIM=${reslim_seconds} ${warmstart_args} --scenario_name="${run_name}_F2050" $opts
else
  gams Balmorel threads=$LSB_DJOB_NUMPROC --USEOPTIONFILE=2 --scenario_name="${run_name}_F2050" $opts
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
    bsub -W 72:00 -env "all, WARMSTART_HOP=${next_hop}, WARMSTART_GDX=${warmstart_gdx}" <../jobs/fullyear_2050.sh
    exit 0
  else
    echo "ERROR: fullyear solve for ${run_name} still hasn't reached optimality after ${MAX_WARMSTART_HOPS} warm-started hops."
    exit 1
  fi
fi

# optimality_check $LSB_JOBID 1

# Submit rolling horizon run
bsub <../jobs/rolling_2050.sh
