#!/bin/sh
# Submit investment.sh for every generated combination scenario.
#
# Usage (from scripts/Balmorel/):
#   ./jobs/slurm/submit_combination_scenarios.sh [scenario ...]
#
# Finds every folder scaffolded by `pixi run create-combination-scenarios`
# (identified by its .combination_scenario.json marker, see docs/adr/0033) and
# submits investment.sh from inside each one - which itself chains to
# fullyear_2050.sh and rolling_2050.sh on completion. Pass scenario names to
# submit only those.
#
# Folders that already hold an _INV result are skipped, since a second
# investment run would overwrite it (one run per type per scenario folder).
# Set FORCE=1 to submit anyway. Plain sbatch loop, no concurrency cap.
set -eu

marker=".combination_scenario.json"

if [ $# -gt 0 ]; then
    scenarios="$*"
else
    scenarios=""
    for marker_file in */"$marker"; do
        [ -f "$marker_file" ] && scenarios="$scenarios ${marker_file%%/*}"
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

submitted=0
skipped=0
for scenario in $scenarios; do
    if [ -f "$scenario/model/MainResults_${scenario}_INV.gdx" ] && [ "${FORCE:-0}" != 1 ]; then
        echo "Skipping $scenario - MainResults_${scenario}_INV.gdx already exists (FORCE=1 to resubmit)"
        skipped=$((skipped + 1))
        continue
    fi
    echo "Submitting $scenario"
    (cd "$scenario" && sbatch ../jobs/slurm/investment.sh)
    submitted=$((submitted + 1))
done

echo "Submitted $submitted, skipped $skipped"
