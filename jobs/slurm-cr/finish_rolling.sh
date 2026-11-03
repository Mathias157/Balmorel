#!/bin/bash
# Finish a rolling job that stopped in penalty_check, after its threshold was raised (GREAT
# docs/adr/0091) or its G2V gate changed (GREAT docs/adr/0097): re-runs the checks at the end of
# rolling_<year>.sh against the job's log and the folder's all_endofmodel.gdx, then returns the
# Year copy like the job would have. Refuses a job
# that stopped for any other reason, or whose folder has a later run of the same name. Since GREAT
# docs/adr/0093 the default threshold is 1e14 for every job again, so set PENALTY_FAIL_ABOVE to
# finish a job that stopped at it.
#
# Usage, on a compute node, from the folder the job ran in (scripts/Balmorel/<scenario>_Y<year>/).
# Not on the login node: it SIGKILLs the verify checks, and once even killed the Year copy's
# rm -rf halfway (2026-11-03). From scripts/Balmorel/:
#   srun --account=dtu_00075 --partition=fatnode --mem=100G --time=04:00:00 --pty bash
#   cd <scenario>_Y<year> && bash ../jobs/slurm-cr/finish_rolling.sh <job id>

source ../jobs/slurm-cr/functions.sh
source ./config.sh

job_id=$1
log=$(echo ../logs/GREAT_rolling_*_${job_id}.out)
if [ ! -f "$log" ]; then
    echo "ERROR: no rolling log ../logs/GREAT_rolling_*_${job_id}.out"
    exit 1
fi
year=$(basename "$log" .out | cut -d_ -f3)
run_name="${source_scenario:-$(basename $PWD)}"

if ! grep -q "^Run name: ${run_name}_R${year} " "$log"; then
    echo "ERROR: job ${job_id} did not run ${run_name}_R${year} - run this from the folder the job ran in"
    exit 1
fi
if ! grep -qE '^ERROR: (objective above PENALTY_FAIL_ABOVE|G2V infrastructure slack above G2V_SLACK_FAIL_ABOVE)' "$log"; then
    echo "ERROR: job ${job_id} did not stop in penalty_check - not finishing it"
    exit 1
fi
# all_endofmodel.gdx and the MainResults belong to the latest run in this folder, which must be this job
for other in ../logs/GREAT_rolling_${year}_*.out; do
    if [ "$other" -nt "$log" ] && grep -q "^Run name: ${run_name}_R${year} " "$other"; then
        echo "ERROR: $(basename "$other") ran ${run_name}_R${year} after job ${job_id} - not finishing ${job_id}"
        exit 1
    fi
done
# Compare physical paths: jobs submitted from a job report /gpfs/hpc-home/..., jobs submitted from
# a login shell /home/... A while loop instead of `| grep -q`, which under pipefail can let a
# match through when squeue gets SIGPIPE.
work_dirs=$(squeue -h -u "$USER" -o '%Z') || { echo "ERROR: squeue failed - not finishing ${job_id}"; exit 1; }
here=$(pwd -P)
while read -r dir; do
    if [ -n "$dir" ] && [ "$(cd "$dir" 2>/dev/null && pwd -P)" = "$here" ]; then
        echo "ERROR: a job is still queued or running in $dir - not finishing ${job_id}"
        exit 1
    fi
done <<< "$work_dirs"

echo "Finishing job ${job_id} (${run_name}_R${year}) at $(date)"
optimality_check $job_id 52
penalty_check $job_id
ccs_storage_check "${run_name}_R${year}"

if [ -f ../jobs/userfunctions.sh ]; then
    . ../jobs/userfunctions.sh
    verifications $run_name
fi

# Year copy only: move results to the source scenario and delete the copy
return_year_copy $year
