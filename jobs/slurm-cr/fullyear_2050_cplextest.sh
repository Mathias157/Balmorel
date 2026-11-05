#!/bin/sh
### General options
### -- specify partition and account --
#SBATCH --partition=fatnode
#SBATCH --account=dtu_00075
### -- set the job Name --
#SBATCH --job-name=GREAT_fullyear_2050_cplextest
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- memory: CR_CORE does not reserve it, only picks nodes with this much in total --
#SBATCH --mem=100G
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=1-00:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=../logs/GREAT_fullyear_2050_cplextest_%j.out
#SBATCH --error=../logs/GREAT_fullyear_2050_cplextest_%j.err

# CPLEX option test for F2050 barrier stalls: the same fullyear 2050 solve as fullyear_2050.sh, but
# with --USEOPTIONFILE=$OPTFILE, in a scratch copy of a Year copy. Submit only via
# jobs/slurm-cr/submit_fullyear_cplextest.sh, which creates that copy and its option file and passes
# OPTFILE, SCENARIO_NAME and REF_JOB.
#
# Differences to fullyear_2050.sh, all deliberate:
# - same cpus, input staging and gams line, so only the option file differs from the reference run;
# - no optimality_check exit, penalty_check or rolling submission: the job ends with a summary of
#   what CPLEX returned, the gate's verdict on it, and (with REF_JOB) whether the barrier replayed
#   the reference run's iterates line for line.

cd "$SLURM_SUBMIT_DIR"

source ../jobs/slurm-cr/functions.sh
source ./config.sh

: "${OPTFILE:?set by submit_fullyear_cplextest.sh}"
: "${SCENARIO_NAME:?set by submit_fullyear_cplextest.sh}"
REF_JOB="${REF_JOB:-}"
require_optfile $OPTFILE

year=2050
log="../logs/GREAT_fullyear_2050_cplextest_${SLURM_JOB_ID}.out"

echo "Starting CPLEX test fullyear simulation at $(date)"
echo "Run name: ${SCENARIO_NAME} (cplex.op${OPTFILE}, ${SLURM_CPUS_PER_TASK} threads${REF_JOB:+, replay of job ${REF_JOB}})"

# Identical input staging to fullyear_2050.sh
/usr/bin/cp -rf simex_INV/* simex/
cat ../base/data/Y_${year}.inc >data/Y.inc
cat ../base/data/T_full.inc >data/T.inc
cat ../base/data/S_all.inc >data/S.inc
cd model
cat balopt_full.opt >balopt.opt
gams Balmorel threads=$SLURM_CPUS_PER_TASK --USEOPTIONFILE=${OPTFILE} --scenario_name="${SCENARIO_NAME}" $opts
cd ..

# Numbered barrier iterates (Itn, primal obj, dual obj, infeasibilities), blanks squeezed
iterates() {
    { grep -aE '^ *[0-9]+ +-?[0-9.]+e[-+][0-9]+ +-?[0-9.]+e[-+][0-9]+ ' "$1" || true; } | tr -s ' '
}

# The job's stdout *is* $log, so the summary must not read $log while printing into it. In round 1
# (jobs 28569-28575) it did: grep refused the file ("input file is also the output", so "Solver
# status: none"), and the replay check read the summary's own "Last barrier iterates" lines back as
# test iterates, so 28569 printed a false REPLAY BROKEN. Read a snapshot instead, and run the gate
# (which reads ../logs/*_<job>.out itself) before the summary starts.
snap=cplextest_log_snapshot.txt
cp "$log" "$snap"
gate=$( (optimality_check $SLURM_JOB_ID 1 strict) 2>&1 || true)

echo
echo "=== CPLEX test summary: ${SCENARIO_NAME} on $(uname -n) ==="
echo "Test lines in model/cplex.op${OPTFILE}:"
sed -n '/^\* Test lines/,$p' "model/cplex.op${OPTFILE}"
echo "Solver status:"
s=$(grep -aE '(LP|MIP|RMIP) status \(' "$snap" || true); echo "${s:-  none in the log}"
echo "Last barrier iterates (Itn, primal, dual, prim inf, upper inf, dual inf, inf ratio - baralg 3 prints no inf ratio):"
iterates "$snap" | tail -n 3
echo "Starred (best) iterate CPLEX went back to, if any:"
s=$(grep -aE '^ *\* +-?[0-9.]+e[-+][0-9]+' "$snap" | tr -s ' ' || true); echo "${s:-  none}"
echo "What GAMS received (model/Balmorel.lst):"
grep -aE '^\*\*\*\* (SOLVER STATUS|MODEL STATUS|OBJECTIVE VALUE)' model/Balmorel.lst || echo "  no solve summary in the listing"
echo "CPLEX solution quality of the returned point (printed only with \"quality 1\"):"
s=$(sed -n '/Solution Quality Statistics:/,/comp\. slackness/p' "$snap" | grep . || true); echo "${s:-  none in the log}"

if [ -n "$REF_JOB" ]; then
    ref_log="../logs/GREAT_fullyear_2050_${REF_JOB}.out"
    iterates "$ref_log" >ref_iterates.txt
    iterates "$snap" >test_iterates.txt
    n=$(wc -l <test_iterates.txt)
    if [ "$n" -gt 0 ] && head -n "$n" ref_iterates.txt | cmp -s - test_iterates.txt; then
        echo "REPLAY: all ${n} barrier iterates identical to job ${REF_JOB}'s"
    else
        echo "REPLAY BROKEN: barrier iterates differ from job ${REF_JOB}'s - first difference (ref <, test >):"
        head -n "$n" ref_iterates.txt | diff - test_iterates.txt | head -n 4 || true
    fi
fi

echo "fullyear_2050.sh's gate would say:"
echo "$gate"
echo "Finished CPLEX test at $(date)"
