#!/bin/sh
# Submit every weather year run for one source scenario, in parallel.
#
# Usage (from scripts/Balmorel/):
#   ./jobs/submit_weather_years.sh <source_scenario> [year]
#
# Finds every <source_scenario>_WY<year>/ folder already scaffolded by
# `pixi run create-weather-year-scenarios <source_scenario>` (see
# docs/adr/0013/0014, CONTEXT.md's "WY folder") and submits
# fullyear_<year>_wy.sh (year defaults to 2050) from inside each one - which
# itself chains to rolling_<year>_wy.sh on completion, same as the ordinary per-scenario
# scripts. Plain sbatch loop, no concurrency cap - see docs/adr/0014's
# consequences for why (untested at the time of writing whether 39 parallel
# jobs is fine on this cluster/account).
set -eu

source_scenario="${1:?Usage: $0 <source_scenario> [year]}"
year="${2:-2050}"

for wy_folder in "${source_scenario}"_WY*/; do
    wy_folder="${wy_folder%/}"
    if [ ! -d "$wy_folder" ]; then
        echo "No ${source_scenario}_WY*/ folders found - run 'pixi run create-weather-year-scenarios ${source_scenario}' first."
        exit 1
    fi
    if [ "$wy_folder" != "base_WY2012" ]; then
        echo "Submitting ${wy_folder} (${year})"
        (cd "$wy_folder" && bsub <../jobs/fullyear_${year}_wy.sh)
    fi
done
