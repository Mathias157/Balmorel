#!/bin/sh
# Reusable error handling for SBATCH job scripts
# Source this file at the beginning of your job script
#
# Computerome copy of jobs/slurm/functions.sh (copied at Balmorel 3ef22af), plus the Year copy
# fan-out/return functions below. Target years run concurrently here, each in its own folder - see
# docs/adr/0046-concurrent-target-years-via-year-copies.md in the GREAT repo.

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

# Function for checking optimality. Status 6 (non-optimal) solves only warn and let the job
# proceed; any other non-optimal status, or fewer/more solves than expected, exits the job.
optimality_check() {
    job_id=$1
    expected_nr=$2
    # Plain grep (not rg) so jobs don't depend on the submitting shell's PATH; || true lets a zero
    # count reach the INFEASIBLE message instead of tripping set -e
    statuses=$(cat ../logs/*_${job_id}.out | grep -oE '(LP|MIP|RMIP) status \([0-9]+\)' || true)
    optimal=$(printf '%s\n' "$statuses" | grep -c 'status (1)' || true)
    nonoptimal=$(printf '%s\n' "$statuses" | grep -c 'status (6)' || true)
    other=$(printf '%s\n' "$statuses" | grep -cvE 'status \((1|6)\)|^$' || true)
    if [[ "$other" -gt 0 ]]; then
        echo "INFEASIBLE: Job ${job_id} had ${other} solves with a status other than 1 (optimal) or 6 (non-optimal):"
        printf '%s\n' "$statuses" | grep -vE 'status \((1|6)\)|^$' | sort | uniq -c
        exit 1
    elif [[ $((optimal + nonoptimal)) -ne "$expected_nr" ]]; then
        echo "INFEASIBLE: Job ${job_id} had ${optimal} optimal and ${nonoptimal} non-optimal solves, which is not the expected ${expected_nr} in total!"
        exit 1
    elif [[ "$nonoptimal" -gt 0 ]]; then
        echo "WARNING: Job ${job_id} had ${nonoptimal} of ${expected_nr} solves end as non-optimal (status 6) - proceeding anyway"
    else
        echo "OPTIMAL: Job ${job_id} had ${optimal} optimal solutions as expected"
    fi
}

# Warn when a solve paid large infeasibility penalties. QOBJ is in money (a clean year is ~2-3e11,
# a clean rolling week ~5e9), and every VQ*/slack term enters it at PENALTYQ (1e9) per unit, so an
# objective above 1e13 means at least ~1e4 units of slack (heat-backup failures gave 1e15-1e16) and
# prices in that solve are not meaningful. Smaller slacks (e.g. the G2V infrastructure slack, ~8e12)
# stay below it. Rolling logs are split per season so the warning names them. See
# docs/adr/0047-backup-heat-in-every-heat-demand-area.md.
# Above PENALTY_FAIL_ABOVE (default 1e14, ~1e5 slack units) the job lists the slacks and exits, so
# no later run is submitted and a Year copy is not returned (docs/adr/0057).
penalty_check() {
    job_id=$1
    fail_above=${PENALTY_FAIL_ABOVE:-1e14}
    if ! cat ../logs/*_${job_id}.out | awk -v fail="$fail_above" '
        /IS3LOOPSET = / { season = $NF }
        /^Objective:/ { n++; if ($2 + 0 > 1e13) { bad++; list = list " " (season == "" ? "full" : season); if ($2 + 0 > max) max = $2 + 0 } }
        END {
            if (bad > 0) printf "WARNING: Job %s had %d of %d solves with objective > 1e13 (max %.3g) - infeasibility slacks active in:%s\n", "'"$job_id"'", bad, n, max, list
            else printf "PENALTY-FREE: Job %s had no solve with objective > 1e13\n", "'"$job_id"'"
            if (max > fail + 0) exit 1
        }'; then
        echo "ERROR: objective above PENALTY_FAIL_ABOVE=${fail_above} - largest slacks:"
        pixi run verify "$PWD" slacks --top 5 || true
        exit 1
    fi
    # Slacks below 1e13 (e.g. under 10 Mt CO2 per solve) pass the objective check, and the next run
    # overwrites all_endofmodel.gdx, so list them now. Report only - some rolling CO2 slack is expected
    # (ADR 0060)
    pixi run verify "$PWD" slacks --top 5 || true
}

# Rolling runs solve one season at a time, so QCCS_STORAGE (the annual CO2 storage limit) is only an
# equation in investment and fullyear runs. Report the rolling year's captured CO2 against it. Report
# only - the rolling year follows the fullyear capacities, which respect the limit. Run from the
# scenario folder. See GREAT docs/adr/0084.
ccs_storage_check() {
    pixi run verify "$PWD" ccs-storage --scenario "$1" --top 5 || true
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

# Years run in their own Year copy (<scenario>_Y<year>); the first year runs in the scenario folder
copy_years="2040 2050"
all_years="2030 $copy_years"

# Start the fullyear -> rolling pair of every target year at once, from a scenario folder whose
# investment run is done. Concurrent runs in one folder would overwrite each other's simex/, data/
# and model/balopt.opt mid-run, so 2040/2050 get a Year copy each. Checks everything before creating
# or submitting anything, so a refusal leaves nothing half-done. With "check" as argument it stops
# after the checks.
fan_out_target_years() {
    scenario="$(basename "$PWD")"
    if [ -n "${source_scenario:-}" ]; then
        echo "ERROR: $scenario is a Year copy of $source_scenario - fan out from $source_scenario instead"
        exit 1
    fi
    if [ ! -d simex_INV ] || [ -z "$(ls -A simex_INV)" ]; then
        echo "ERROR: $scenario has no simex_INV - run its investment run first"
        exit 1
    fi
    for year in $all_years; do
        for run in F R; do
            if [ -f "model/MainResults_${scenario}_${run}${year}.gdx" ]; then
                echo "ERROR: $scenario already has MainResults_${scenario}_${run}${year}.gdx - remove it to rerun"
                exit 1
            fi
        done
    done
    for year in $copy_years; do
        if [ -e "../${scenario}_Y${year}" ]; then
            echo "ERROR: ../${scenario}_Y${year} already exists, probably from a failed run - check it and delete it first"
            exit 1
        fi
    done
    if [ "${1:-}" = check ]; then
        return 0
    fi

    for year in $copy_years; do
        copy="../${scenario}_Y${year}"
        mkdir -p "$copy/model" "$copy/simex"
        # config.sh carries the source scenario's identity, so results are named after it
        cp config.sh "$copy/config.sh"
        printf '\n# Year copy of %s, see jobs/slurm-cr/functions.sh\nsource_scenario=%s\n' "$scenario" "$scenario" >>"$copy/config.sh"
        cp -r data "$copy/data"
        cp -r simex_INV "$copy/simex_INV"
        # Top-level model files only: leaves out GAMS scratch dirs (225*), results and listings
        find model -maxdepth 1 -type f ! -name '*.gdx' ! -name '*.lst' ! -name '*.log' ! -name 'balopt.opt' \
            -exec cp {} "$copy/model/" \;
        echo "Created Year copy $copy"
    done

    sbatch ../jobs/slurm-cr/fullyear_2030.sh
    for year in $copy_years; do
        (cd "../${scenario}_Y${year}" && sbatch "../jobs/slurm-cr/fullyear_${year}.sh")
    done
}

# Move a Year copy's fullyear and rolling MainResults into its source scenario's model/ and delete
# the copy. Call from the scenario folder at the end of a successful rolling run - does nothing when
# that folder is the source scenario itself. On any failure the copy is left as it is.
return_year_copy() {
    year=$1
    if [ -z "${source_scenario:-}" ]; then
        return 0
    fi
    copy="$(basename "$PWD")"
    if [ "$copy" != "${source_scenario}_Y${year}" ]; then
        echo "ERROR: expected to be in ${source_scenario}_Y${year}, but in $copy - not moving or deleting anything"
        exit 1
    fi
    if [ ! -d "../${source_scenario}/model" ]; then
        echo "ERROR: source scenario ../${source_scenario}/model not found - leaving $copy as it is"
        exit 1
    fi
    for run in F R; do
        result="MainResults_${source_scenario}_${run}${year}.gdx"
        if [ ! -f "model/$result" ]; then
            echo "ERROR: model/$result missing - leaving $copy as it is"
            exit 1
        fi
        if [ -e "../${source_scenario}/model/$result" ]; then
            echo "ERROR: ../${source_scenario}/model/$result already exists - leaving $copy as it is"
            exit 1
        fi
    done
    for run in F R; do
        mv "model/MainResults_${source_scenario}_${run}${year}.gdx" "../${source_scenario}/model/"
    done
    cd ..
    rm -rf "$copy"
    echo "Moved ${source_scenario}_F${year}/_R${year} results to ${source_scenario} and deleted $copy"
}

# Get user settings and paths to GAMS
if [ ! -f "../.env" ]; then
    echo "No .env file found! Make one and define:
  GAMS_SYSTEM_DIR=...
  "
    exit 1
fi
source ../.env
export PATH=$GAMS_SYSTEM_DIR:$PATH
export LD_LIBRARY_PATH=$GAMS_SYSTEM_DIR:${LD_LIBRARY_PATH:-}
