#!/bin/sh
# Submit investment.sh for every generated combination scenario.
#
# Usage (from scripts/Balmorel/):
#   ./jobs/slurm-cr/submit_combination_scenarios.sh [scenario ...]
#
# Finds every folder scaffolded by `pixi run create-combination-scenarios`
# (identified by its .combination_scenario.json marker, see docs/adr/0033) and
# submits investment.sh from inside each one - which itself chains to
# fan_out_target_years (all target years at once) on completion. Pass scenario names to
# submit only those. base (the marker without switches) is the reference run and is only
# submitted when named: the sweep's caps are recalibrated from base_INV first (ADR 0040).
#
# Folders that already hold an _INV result are skipped, since a second
# investment run would overwrite it (one run per type per scenario folder).
# Set FORCE=1 to submit anyway. Plain sbatch loop, no concurrency cap.
#
# Every scenario to submit is checked first: if old target-year results (_F/_R) or Year copies
# (_Y20xx) exist, fan_out_target_years would refuse at the end of the investment run, so nothing
# is submitted and the paths to archive are listed.
set -eu

marker=".combination_scenario.json"
# FORCE=1
# Scenarios with at least this many switches get a longer walltime: ALLN's investment run took
# over 1.5 days, past investment.sh's 16 h
long_switches=3
long_time="2-00:00:00"

# Number of switches in a scenario's marker (0 for base)
switch_count() {
    tr -d ' \n' <"$1/$marker" | sed 's/.*"switches":\[\([^]]*\)\].*/\1/' | tr ',' '\n' | grep -c '"' || true
}

# What fan_out_target_years (functions.sh) refuses on, one path per line: results of the target
# years in the folder and leftover Year copies. Its simex_INV check is left out, since simex_INV
# only exists after the investment run.
leftovers() {
    (
        cd "$1"
        . ../jobs/slurm-cr/functions.sh
        for year in $all_years; do
            for run in F R; do
                if [ -f "model/MainResults_${1}_${run}${year}.gdx" ]; then
                    echo "$1/model/MainResults_${1}_${run}${year}.gdx"
                fi
            done
        done
        for year in $copy_years; do
            if [ -e "../${1}_Y${year}" ]; then
                echo "${1}_Y${year}"
            fi
        done
    )
}

if [ $# -gt 0 ]; then
    scenarios="$*"
else
    scenarios=""
    for marker_file in */"$marker"; do
        scenario="${marker_file%%/*}"
        if [ -f "$marker_file" ] && [ "$(switch_count "$scenario")" -gt 0 ]; then
            scenarios="$scenarios $scenario"
        fi
    done
fi

if [ -z "$scenarios" ]; then
    echo "No combination scenario folders found - run 'pixi run create-combination-scenarios' first."
    exit 1
fi

# Validate every name before submitting anything, so a typo doesn't leave half a batch submitted
for scenario in $scenarios; do
    if [ ! -f "$scenario/$marker" ]; then
        echo "ERROR: $scenario is not a generated combination scenario folder (no $marker)"
        exit 1
    fi
done

to_submit=""
skipped=0
for scenario in $scenarios; do
    if [ -f "$scenario/model/MainResults_${scenario}_INV.gdx" ] && [ "${FORCE:-0}" != 1 ]; then
        echo "Skipping $scenario - MainResults_${scenario}_INV.gdx already exists (FORCE=1 to resubmit)"
        skipped=$((skipped + 1))
        continue
    fi
    to_submit="$to_submit $scenario"
done

# Refuse the whole batch before submitting anything if a fan-out would refuse later. leftovers
# sources functions.sh, which needs the .env the jobs use
if [ ! -f .env ]; then
    echo "ERROR: no .env in $(pwd) - the job scripts need it (see jobs/slurm-cr/functions.sh)"
    exit 1
fi
stale=""
for scenario in $to_submit; do
    stale="$stale$(leftovers "$scenario")
"
done
stale=$(echo "$stale" | sed '/^$/d')
if [ -n "$stale" ]; then
    echo "ERROR: nothing submitted - fan_out_target_years would refuse after the investment run."
    echo "Archive or remove these first:"
    echo "$stale" | sed 's/^/  /'
    exit 1
fi

submitted=0
for scenario in $to_submit; do
    if [ "$(switch_count "$scenario")" -ge "$long_switches" ]; then
        echo "Submitting $scenario (walltime $long_time)"
        (cd "$scenario" && sbatch --time="$long_time" ../jobs/slurm-cr/investment.sh)
    else
        echo "Submitting $scenario"
        (cd "$scenario" && sbatch ../jobs/slurm-cr/investment.sh)
    fi
    submitted=$((submitted + 1))
done

echo "Submitted $submitted, skipped $skipped"
