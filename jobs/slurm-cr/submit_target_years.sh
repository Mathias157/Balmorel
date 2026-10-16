#!/bin/sh
# Start the fullyear/rolling runs of every target year for combination scenarios whose investment
# run is already done.
#
# Usage (from scripts/Balmorel/):
#   ./jobs/slurm-cr/submit_target_years.sh [scenario ...]
#
# Runs fan_out_target_years (functions.sh) inside each scenario folder - the same thing
# investment.sh does at its end: fullyear_2030.sh in the folder itself, and fullyear_2040.sh/
# fullyear_2050.sh in fresh Year copies <scenario>_Y2040/<scenario>_Y2050. Without arguments, takes
# every generated combination scenario folder (.combination_scenario.json marker, see docs/adr/0033)
# with a non-empty simex_INV/. Only simex_INV/ is needed to run the target years - the _INV
# MainResults may live on another cluster.
#
# Every scenario is checked before anything is submitted, so one refusal (existing _F/_R result,
# leftover Year copy, missing simex_INV) stops the whole batch instead of half of it.
set -eu

marker=".combination_scenario.json"

if [ $# -gt 0 ]; then
    scenarios="$*"
else
    scenarios=""
    for marker_file in */"$marker"; do
        scenario="${marker_file%%/*}"
        [ -n "$(ls -A "$scenario/simex_INV" 2>/dev/null)" ] && scenarios="$scenarios $scenario"
    done
fi

if [ -z "$scenarios" ]; then
    echo "No combination scenario folders with a simex_INV found."
    exit 1
fi

for scenario in $scenarios; do
    if [ ! -f "$scenario/$marker" ]; then
        echo "ERROR: $scenario is not a generated combination scenario folder (no $marker)"
        exit 1
    fi
    (cd "$scenario" && . ../jobs/slurm-cr/functions.sh && . ./config.sh && fan_out_target_years check)
done

submitted=0
for scenario in $scenarios; do
    echo "Submitting $scenario"
    (cd "$scenario" && . ../jobs/slurm-cr/functions.sh && . ./config.sh && fan_out_target_years)
    submitted=$((submitted + 1))
done

echo "Fanned out $submitted scenarios"
