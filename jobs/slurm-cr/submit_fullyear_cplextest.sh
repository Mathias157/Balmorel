#!/bin/sh
# Re-run a scenario's fullyear 2050 solve with extra CPLEX options, in a scratch copy of its Year copy,
# to test settings against F2050 barrier stalls (CPLEX status 6, returning its "*" best iterate).
#
# Usage (from scripts/Balmorel/, on Computerome):
#   [REF_JOB=<job id>] ./jobs/slurm-cr/submit_fullyear_cplextest.sh <scenario> <tag> "<cplex option>" ["<cplex option>" ...]
#   e.g. REF_JOB=27255 ./jobs/slurm-cr/submit_fullyear_cplextest.sh ALLN it250 "baritlim 250"
#        ./jobs/slurm-cr/submit_fullyear_cplextest.sh HPNH2N ne1 "numericalemphasis 1" "quality 1"
#
# Creates CPXTEST_F2050_<tag>_<scenario>/ as a sibling of <scenario>_Y2050 instead of re-running inside
# the Year copy: parallel tests would overwrite each other there, and a test result must never be
# mistaken for the scenario's own F2050 (docs/adr/0023, 0046). The copy gets the Year copy's data/,
# simex/, simex_INV/, config.sh and top-level model files, so the LP is the one the Year copy's own
# fullyear run built. The test option file is cplex.op5: the Year copy's cplex.op7 (the F2050 setting,
# docs/adr/0096) with the given lines appended, so the only difference to the reference run is those
# lines. Its results are named <folder>_F2050, so they cannot collide with a real scenario name.
#
# REF_JOB, if set, is the reference F2050 job: the test job then reports whether its barrier iterates
# reproduce the reference's line for line (a deterministic replay, needed for baritlim tests).
#
# Delete the CPXTEST_* folder once compared: pybalmorel scans every scenario folder, so it would
# otherwise show up in analyse.py's all-scenario commands.
set -eu

usage="Usage: [REF_JOB=<job id>] $0 <scenario> <tag> \"<cplex option>\" [\"<cplex option>\" ...]"
scenario="${1:?$usage}"
tag="${2:?$usage}"
shift 2
if [ "$#" -eq 0 ]; then
    echo "$usage"
    echo "Give at least one CPLEX option line - without one the test would only repeat cplex.op7."
    exit 1
fi

scenario="${scenario%/}"
source_folder="${scenario}_Y2050"
target="CPXTEST_F2050_${tag}_${scenario}"
optfile=5

case "$tag" in
    *[!A-Za-z0-9]*) echo "Tag '${tag}' must be alphanumeric - it becomes part of the folder and result names."; exit 1 ;;
esac
if [ ! -d "$source_folder" ]; then
    echo "${source_folder} does not exist - this tests F2050 runs, which run in the Year copy."
    exit 1
fi
if [ -z "$(ls -A "${source_folder}/simex_INV" 2>/dev/null)" ]; then
    echo "${source_folder}/simex_INV is empty - the fullyear run needs the investment run's simex files."
    exit 1
fi
if [ ! -f "${source_folder}/model/cplex.op7" ]; then
    echo "${source_folder}/model/cplex.op7 is missing - nothing to base the test option file on."
    exit 1
fi
if [ -n "${REF_JOB:-}" ] && [ ! -f "logs/GREAT_fullyear_2050_${REF_JOB}.out" ]; then
    echo "logs/GREAT_fullyear_2050_${REF_JOB}.out does not exist - check REF_JOB."
    exit 1
fi
if [ -e "$target" ]; then
    echo "${target} already exists - delete it or pick another tag. Refusing to put a second _F2050 run in one folder."
    exit 1
fi

mkdir -p "${target}/model"
/usr/bin/cp -f "${source_folder}/config.sh" "${target}/config.sh"
/usr/bin/cp -r "${source_folder}/data" "${target}/data"
/usr/bin/cp -r "${source_folder}/simex_INV" "${target}/simex_INV"
# simex/ as the Year copy has it: the job overlays simex_INV/ on it, as fullyear_2050.sh does
/usr/bin/cp -r "${source_folder}/simex" "${target}/simex"
# Top-level model files only, as fan_out_target_years copies them: no GAMS scratch dirs, results or listings
find "${source_folder}/model" -maxdepth 1 -type f ! -name '*.gdx' ! -name '*.lst' ! -name '*.log' ! -name 'balopt.opt' \
    -exec /usr/bin/cp {} "${target}/model/" \;

{
    printf '* CPLEX test option file written by jobs/slurm-cr/submit_fullyear_cplextest.sh at %s:\n' "$(date '+%F %T')"
    printf '* %s/model/cplex.op7 with the test lines below appended.\n' "$source_folder"
    cat "${source_folder}/model/cplex.op7"
    printf '\n* Test lines (tag %s)\n' "$tag"
    for line in "$@"; do
        printf '%s\n' "$line"
    done
} >"${target}/model/cplex.op${optfile}"

export_vars="ALL,OPTFILE=${optfile},SCENARIO_NAME=${target}_F2050"
if [ -n "${REF_JOB:-}" ]; then
    export_vars="${export_vars},REF_JOB=${REF_JOB}"
fi
echo "Submitting ${target} (cplex.op7 + $*${REF_JOB:+, replay of job ${REF_JOB}})"
(cd "$target" && sbatch --export="$export_vars" ../jobs/slurm-cr/fullyear_2050_cplextest.sh)
