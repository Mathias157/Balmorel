#!/bin/sh
# Reusable error handling for BSUB job scripts
# Source this file at the beginning of your job script

# Exit on error, unset variables, and pipeline failures
set -e
set -u
set -o pipefail

# Trap signals and errors to prevent further execution
cleanup() {
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "ERROR: Job failed with exit code $exit_code at $(date)"
        echo "Stopping execution - no further jobs will be submitted"
    fi
    exit $exit_code
}

trap cleanup EXIT SIGTERM SIGINT

# Function for checking optimality. Status 5 (optimal with unscaled infeasibilities) and 6
# (non-optimal) solves only warn and let the job proceed; any other non-optimal status, or
# fewer/more solves than expected, exits the job.
optimality_check() {
    job_id=$1
    expected_nr=$2
    # Plain grep (not rg) so jobs don't depend on the submitting shell's PATH; || true lets a zero
    # count reach the INFEASIBLE message instead of tripping set -e
    statuses=$(cat ../logs/*_${job_id}.out | grep -oE '(LP|MIP|RMIP) status \([0-9]+\)' || true)
    optimal=$(printf '%s\n' "$statuses" | grep -c 'status (1)' || true)
    unscaled=$(printf '%s\n' "$statuses" | grep -c 'status (5)' || true)
    nonoptimal=$(printf '%s\n' "$statuses" | grep -c 'status (6)' || true)
    other=$(printf '%s\n' "$statuses" | grep -cvE 'status \((1|5|6)\)|^$' || true)
    if [[ "$other" -gt 0 ]]; then
        echo "INFEASIBLE: Job ${job_id} had ${other} solves with a status other than 1 (optimal), 5 (unscaled infeasibilities) or 6 (non-optimal):"
        printf '%s\n' "$statuses" | grep -vE 'status \((1|5|6)\)|^$' | sort | uniq -c
        exit 1
    elif [[ $((optimal + unscaled + nonoptimal)) -ne "$expected_nr" ]]; then
        echo "INFEASIBLE: Job ${job_id} had ${optimal} optimal, ${unscaled} unscaled-infeasible and ${nonoptimal} non-optimal solves, which is not the expected ${expected_nr} in total!"
        exit 1
    elif [[ $((unscaled + nonoptimal)) -gt 0 ]]; then
        echo "WARNING: Job ${job_id} had ${unscaled} of ${expected_nr} solves end optimal with unscaled infeasibilities (status 5) and ${nonoptimal} as non-optimal (status 6) - proceeding anyway"
    else
        echo "OPTIMAL: Job ${job_id} had ${optimal} optimal solutions as expected"
    fi
}

# Stop before GAMS runs if the scenario folder lacks the CPLEX option file the job asks for - CPLEX
# only warns about a missing option file and then solves with its own defaults. Run from the
# scenario folder. See docs/adr/0035-fullyear-and-rolling-use-cplex-op8.md.
require_optfile() {
    if [ ! -f "model/cplex.op$1" ]; then
        echo "model/cplex.op$1 is missing - copy it from ../base/model/ first."
        exit 1
    fi
}

# Get user settings and paths to GAMS 50.4.1
source ../.env
if not [ -f "../.env" ]; then
    echo "No .env file found! Make one and define:
  GAMS_SYSTEM_DIR=...
  "
    exit 1
fi
export PATH=$GAMS_SYSTEM_DIR:$PATH
export LD_LIBRARY_PATH=$GAMS_SYSTEM_DIR:$LD_LIBRARY_PATH
