#!/bin/sh
### General options
### -- specify partition --
#SBATCH --partition=windfatq
### -- set the job Name --
#SBATCH --job-name=analysis
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=2
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=0-24:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/analysis_%j.out
#SBATCH --error=logs/analysis_%j.err

cd "$SLURM_SUBMIT_DIR"

source ~/.bashrc

export GAMS_SYSTEM_DIR=/groups/INP/gams/gams53.4_linux_x64_64_sfx/
export PATH=$GAMS_SYSTEM_DIR:$PATH
export LD_LIBRARY_PATH=$GAMS_SYSTEM_DIR:${LD_LIBRARY_PATH:-}

conda activate great

# Load error handling and GAMS paths
# source jobs/slurm/functions.sh

# Load user functions (generate_plots)
# source jobs/userfunctions.sh
# Get scenario choice and run name from jobs/scenario_choice.sh
# source jobs/scenario_choice.sh

# snakemake -s rules/postprocess.smk

python analysis/analyse.py --overwrite combined-costs \
    --scenarios ALLN \
    --scenarios DCN \
    --scenarios EIN \
    --scenarios ELN \
    --scenarios EVN \
    --scenarios EVNEIN \
    --scenarios EVNH2N \
    --scenarios EVNHPN \
    --scenarios EVNTPN \
    --scenarios H2N \
    --scenarios HPN \
    --scenarios HSN \
    --scenarios HSNSSN \
    --scenarios NPY \
    --scenarios SSN \
    --scenarios TPN \
    --scenarios logs \
    --scenarios archiv \
    --scenarios D100 \
    --scenarios D25 \
    --scenarios D25VGN \
    --scenarios D50 \
    --scenarios PVN \
    --scenarios EINDCN \
    --scenarios EINELN \
    --scenarios EINH2N \
    --scenarios EINHSN \
    --scenarios EINNPY \
    --scenarios EINSSN \
    --scenarios EINTPN \
    --scenarios ELNDCN \
    --scenarios ELNHSN \
    --scenarios ELNNPY \
    --scenarios ELNSSN \
    --scenarios EVNDCN \
    --scenarios EVNELN \
    --scenarios EVNFEN \
    --scenarios EVNHSN \
    --scenarios EVNNPY \
    --scenarios EVNSSN \
    --scenarios FEN \
    --scenarios FENDCN \
    --scenarios FENEIN \
    --scenarios FENELN \
    --scenarios FENH2N \
    --scenarios FENHPN \
    --scenarios FENHSN \
    --scenarios FENNPY \
    --scenarios FENSSN \
    --scenarios FENTPN \
    --scenarios H2NDCN \
    --scenarios H2NELN \
    --scenarios H2NHSN \
    --scenarios H2NNPY \
    --scenarios H2NSSN \
    --scenarios HPNDCN \
    --scenarios HPNEIN \
    --scenarios HPNELN \
    --scenarios HPNH2N \
    --scenarios HPNHSN \
    --scenarios HPNNPY \
    --scenarios HPNSSN \
    --scenarios HPNTPN \
    --scenarios HSNDCN \
    --scenarios NPYDCN \
    --scenarios NPYHSN \
    --scenarios NPYSSN \
    --scenarios PVNDCN \
    --scenarios PVNEIN \
    --scenarios PVNELN \
    --scenarios PVNEVN \
    --scenarios PVNFEN \
    --scenarios PVNH2N \
    --scenarios PVNHPN \
    --scenarios PVNHSN \
    --scenarios PVNNPY \
    --scenarios PVNSSN \
    --scenarios PVNTPN \
    --scenarios SSNDCN \
    --scenarios TPNDCN \
    --scenarios TPNELN \
    --scenarios TPNH2N \
    --scenarios TPNHSN \
    --scenarios TPNNPY \
    --scenarios TPNSSN \
    --scenarios base

python scripts/postprocessing/estimate_flexibility_needs.py \
    --output-dir build_postprocess_COMBSC \
    --scenarios ALLN \
    --scenarios DCN \
    --scenarios EIN \
    --scenarios ELN \
    --scenarios EVN \
    --scenarios EVNEIN \
    --scenarios EVNH2N \
    --scenarios EVNHPN \
    --scenarios EVNTPN \
    --scenarios H2N \
    --scenarios HPN \
    --scenarios HSN \
    --scenarios HSNSSN \
    --scenarios NPY \
    --scenarios SSN \
    --scenarios TPN \
    --scenarios logs \
    --scenarios archiv \
    --scenarios D100 \
    --scenarios D25 \
    --scenarios D25VGN \
    --scenarios D50 \
    --scenarios PVN \
    --scenarios EINDCN \
    --scenarios EINELN \
    --scenarios EINH2N \
    --scenarios EINHSN \
    --scenarios EINNPY \
    --scenarios EINSSN \
    --scenarios EINTPN \
    --scenarios ELNDCN \
    --scenarios ELNHSN \
    --scenarios ELNNPY \
    --scenarios ELNSSN \
    --scenarios EVNDCN \
    --scenarios EVNELN \
    --scenarios EVNFEN \
    --scenarios EVNHSN \
    --scenarios EVNNPY \
    --scenarios EVNSSN \
    --scenarios FEN \
    --scenarios FENDCN \
    --scenarios FENEIN \
    --scenarios FENELN \
    --scenarios FENH2N \
    --scenarios FENHPN \
    --scenarios FENHSN \
    --scenarios FENNPY \
    --scenarios FENSSN \
    --scenarios FENTPN \
    --scenarios H2NDCN \
    --scenarios H2NELN \
    --scenarios H2NHSN \
    --scenarios H2NNPY \
    --scenarios H2NSSN \
    --scenarios HPNDCN \
    --scenarios HPNEIN \
    --scenarios HPNELN \
    --scenarios HPNH2N \
    --scenarios HPNHSN \
    --scenarios HPNNPY \
    --scenarios HPNSSN \
    --scenarios HPNTPN \
    --scenarios HSNDCN \
    --scenarios NPYDCN \
    --scenarios NPYHSN \
    --scenarios NPYSSN \
    --scenarios PVNDCN \
    --scenarios PVNEIN \
    --scenarios PVNELN \
    --scenarios PVNEVN \
    --scenarios PVNFEN \
    --scenarios PVNH2N \
    --scenarios PVNHPN \
    --scenarios PVNHSN \
    --scenarios PVNNPY \
    --scenarios PVNSSN \
    --scenarios PVNTPN \
    --scenarios SSNDCN \
    --scenarios TPNDCN \
    --scenarios TPNELN \
    --scenarios TPNH2N \
    --scenarios TPNHSN \
    --scenarios TPNNPY \
    --scenarios TPNSSN \
    --scenarios base
