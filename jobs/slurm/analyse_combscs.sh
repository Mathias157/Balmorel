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
    --scenarios ALLN_R2030 \
    --scenarios DCN_R2030 \
    --scenarios EIN_R2030 \
    --scenarios ELN_R2030 \
    --scenarios EVN_R2030 \
    --scenarios EVNEIN_R2030 \
    --scenarios EVNH2N_R2030 \
    --scenarios EVNHPN_R2030 \
    --scenarios EVNTPN_R2030 \
    --scenarios H2N_R2030 \
    --scenarios HPN_R2030 \
    --scenarios HSN_R2030 \
    --scenarios HSNSSN_R2030 \
    --scenarios NPY_R2030 \
    --scenarios SSN_R2030 \
    --scenarios TPN_R2030 \
    --scenarios logs_R2030 \
    --scenarios archiv_R2030 \
    --scenarios D100_R2030 \
    --scenarios D25_R2030 \
    --scenarios D25VGN_R2030 \
    --scenarios D50_R2030 \
    --scenarios PVN_R2030 \
    --scenarios EINDCN_R2030 \
    --scenarios EINELN_R2030 \
    --scenarios EINH2N_R2030 \
    --scenarios EINHSN_R2030 \
    --scenarios EINNPY_R2030 \
    --scenarios EINSSN_R2030 \
    --scenarios EINTPN_R2030 \
    --scenarios ELNDCN_R2030 \
    --scenarios ELNHSN_R2030 \
    --scenarios ELNNPY_R2030 \
    --scenarios ELNSSN_R2030 \
    --scenarios EVNDCN_R2030 \
    --scenarios EVNELN_R2030 \
    --scenarios EVNFEN_R2030 \
    --scenarios EVNHSN_R2030 \
    --scenarios EVNNPY_R2030 \
    --scenarios EVNSSN_R2030 \
    --scenarios FEN_R2030 \
    --scenarios FENDCN_R2030 \
    --scenarios FENEIN_R2030 \
    --scenarios FENELN_R2030 \
    --scenarios FENH2N_R2030 \
    --scenarios FENHPN_R2030 \
    --scenarios FENHSN_R2030 \
    --scenarios FENNPY_R2030 \
    --scenarios FENSSN_R2030 \
    --scenarios FENTPN_R2030 \
    --scenarios H2NDCN_R2030 \
    --scenarios H2NELN_R2030 \
    --scenarios H2NHSN_R2030 \
    --scenarios H2NNPY_R2030 \
    --scenarios H2NSSN_R2030 \
    --scenarios HPNDCN_R2030 \
    --scenarios HPNEIN_R2030 \
    --scenarios HPNELN_R2030 \
    --scenarios HPNH2N_R2030 \
    --scenarios HPNHSN_R2030 \
    --scenarios HPNNPY_R2030 \
    --scenarios HPNSSN_R2030 \
    --scenarios HPNTPN_R2030 \
    --scenarios HSNDCN_R2030 \
    --scenarios NPYDCN_R2030 \
    --scenarios NPYHSN_R2030 \
    --scenarios NPYSSN_R2030 \
    --scenarios PVNDCN_R2030 \
    --scenarios PVNEIN_R2030 \
    --scenarios PVNELN_R2030 \
    --scenarios PVNEVN_R2030 \
    --scenarios PVNFEN_R2030 \
    --scenarios PVNH2N_R2030 \
    --scenarios PVNHPN_R2030 \
    --scenarios PVNHSN_R2030 \
    --scenarios PVNNPY_R2030 \
    --scenarios PVNSSN_R2030 \
    --scenarios PVNTPN_R2030 \
    --scenarios SSNDCN_R2030 \
    --scenarios TPNDCN_R2030 \
    --scenarios TPNELN_R2030 \
    --scenarios TPNH2N_R2030 \
    --scenarios TPNHSN_R2030 \
    --scenarios TPNNPY_R2030 \
    --scenarios TPNSSN_R2030 \
    --scenarios base_R2030
