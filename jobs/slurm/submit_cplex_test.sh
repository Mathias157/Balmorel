#!/bin/sh
# Re-run a completed weather year rolling 2050 run with a different CPLEX option file, for timing and
# result comparison against the original.
#
# Usage (from scripts/Balmorel/, on HPC):
#   ./jobs/slurm/submit_cplex_test.sh <wy_folder> <optfile_nr> [cpus]
#   e.g. ./jobs/slurm/submit_cplex_test.sh PVN_WY2012 7
#
# Creates CPXTEST_op<optfile_nr>_n<cpus>_<wy_folder>/ as a sibling folder instead of re-running inside
# <wy_folder>: a second _R2050 there would break the one-run-per-type rule that postprocessing's
# per-folder GDX caching relies on (docs/adr/0023). The copy gets <wy_folder>'s data/, simex/ (already
# holding the fullyear run's storage levels, which the rolling step reads but never writes) and
# config.sh, the static model files, and base/model/cplex.op<optfile_nr> - no result GDX, so the new
# folder only ever holds this one test run.
#
# cpus defaults to 10, matching rolling_2050_wy.sh, so only the option file differs from the
# reference run. Delete the CPXTEST_* folder once compared: pybalmorel scans every scenario folder, so
# it would otherwise show up in analyse.py's all-scenario commands.
set -eu

source_folder="${1:?Usage: $0 <wy_folder> <optfile_nr> [cpus]}"
optfile="${2:?Usage: $0 <wy_folder> <optfile_nr> [cpus]}"
cpus="${3:-10}"

source_folder="${source_folder%/}"
case "$source_folder" in
    *_WY[0-9][0-9][0-9][0-9]) weather_year="${source_folder##*_WY}" ;;
    *) echo "Expected a <scenario>_WY<year> folder, got '${source_folder}'."; exit 1 ;;
esac

target="CPXTEST_op${optfile}_n${cpus}_${source_folder}"

if [ ! -f "base/model/cplex.op${optfile}" ]; then
    echo "base/model/cplex.op${optfile} does not exist."
    exit 1
fi
if [ -z "$(ls -A "${source_folder}/simex" 2>/dev/null)" ]; then
    echo "${source_folder}/simex is empty - its fullyear run has to have completed first."
    exit 1
fi
if [ -e "$target" ]; then
    echo "${target} already exists - delete it or pick another option file/cpus. Refusing to put a second _R2050 run in one folder."
    exit 1
fi

mkdir -p "${target}/data" "${target}/model" "${target}/simex"
/usr/bin/cp -f "${source_folder}"/data/* "${target}/data/"
/usr/bin/cp -rf "${source_folder}"/simex/* "${target}/simex/"
/usr/bin/cp -f "${source_folder}/config.sh" "${target}/config.sh"
/usr/bin/cp -f "${source_folder}/model/Balmorel.gms" "${source_folder}/model/balopt_roll.opt" "${target}/model/"
/usr/bin/cp -f "base/model/cplex.op${optfile}" "${target}/model/"

echo "Submitting ${target} (weather year ${weather_year}, cplex.op${optfile}, ${cpus} cpus)"
(cd "$target" && sbatch --cpus-per-task="$cpus" \
    --export=ALL,WEATHER_YEAR="$weather_year",OPTFILE="$optfile",SCENARIO_NAME="${target}_R2050" \
    ../jobs/slurm/rolling_2050_wy_cplextest.sh)
