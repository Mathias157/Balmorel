#!/bin/sh
### General options
### -- specify partition and account --
#SBATCH --partition=fatnode
#SBATCH --account=dtu_00075
### -- set the job Name --
#SBATCH --job-name=combscs_analysis
### -- ask for number of cpus (default: 1) --
#SBATCH --cpus-per-task=10
### -- specify that the cpus must be on the same node --
#SBATCH --nodes=1
### -- memory: CR_CORE does not reserve it, only picks nodes with this much in total --
#SBATCH --mem=100G
### -- set walltime limit: D-HH:MM:SS --
#SBATCH --time=1-12:00:00
### -- send notification at completion --
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mberos@dtu.dk
### -- Specify the output and error file. %j is the job-id --
#SBATCH --output=logs/combscs_analysis_%j.out
#SBATCH --error=logs/combscs_analysis_%j.err

cd "$SLURM_SUBMIT_DIR"

# Load error handling and GAMS paths
# source jobs/slurm/functions.sh

# Load user functions (generate_plots)
# source jobs/userfunctions.sh
# Get scenario choice and run name from jobs/scenario_choice.sh
# source jobs/scenario_choice.sh

# snakemake -s rules/postprocess.smk

pixi run analyse --overwrite --filters 'Scenario.str.contains("INV") and Year == "2030"' production --filename "production_investment_runs_2030"
pixi run analyse --filters 'Scenario.str.contains("INV") and Year == "2040"' production --filename "production_investment_runs_2040"
pixi run analyse --filters 'Scenario.str.contains("INV") and Year == "2050"' production --filename "production_investment_runs_2050"
pixi run analyse --filters 'Scenario.str.contains("R2030")' production --filename "production_r2030_runs"
pixi run analyse --filters 'Scenario.str.contains("R2040")' production --filename "production_r2040_runs"
pixi run analyse --filters 'Scenario.str.contains("R2050")' production --filename "production_r2050_runs"

pixi run analyse --overwrite --filters 'Scenario.str.contains("INV") and Year == "2030"' costs --filename "costs_investment_runs_2030"
pixi run analyse --filters 'Scenario.str.contains("INV") and Year == "2040"' costs --filename "costs_investment_runs_2040"
pixi run analyse --filters 'Scenario.str.contains("INV") and Year == "2050"' costs --filename "costs_investment_runs_2050"
pixi run analyse --filters 'Scenario.str.contains("R2030")' costs --filename "costs_r2030_runs"
pixi run analyse --filters 'Scenario.str.contains("R2040")' costs --filename "costs_r2040_runs"
pixi run analyse --filters 'Scenario.str.contains("R2050")' costs --filename "costs_r2050_runs"

pixi run analyse --overwrite --filters 'Scenario.str.contains("INV") and Year == "2030"' cap --filename "cap_2030"
pixi run analyse --filters 'Scenario.str.contains("INV") and Year == "2040"' cap --filename "cap_2040"
pixi run analyse --filters 'Scenario.str.contains("INV") and Year == "2050"' cap --filename "cap_2050"

pixi run analyse --overwrite combined-costs \
    --scenarios ALLN_R2030 \
    --scenarios ALLNNPY_R2030 \
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

pixi run analyse --overwrite combined-costs \
    --scenarios ALLN_R2040 \
    --scenarios ALLNNPY_R2040 \
    --scenarios DCN_R2040 \
    --scenarios EIN_R2040 \
    --scenarios ELN_R2040 \
    --scenarios EVN_R2040 \
    --scenarios EVNEIN_R2040 \
    --scenarios EVNH2N_R2040 \
    --scenarios EVNHPN_R2040 \
    --scenarios EVNTPN_R2040 \
    --scenarios H2N_R2040 \
    --scenarios HPN_R2040 \
    --scenarios HSN_R2040 \
    --scenarios HSNSSN_R2040 \
    --scenarios NPY_R2040 \
    --scenarios SSN_R2040 \
    --scenarios TPN_R2040 \
    --scenarios D100_R2040 \
    --scenarios D25_R2040 \
    --scenarios D25VGN_R2040 \
    --scenarios D50_R2040 \
    --scenarios PVN_R2040 \
    --scenarios EINDCN_R2040 \
    --scenarios EINELN_R2040 \
    --scenarios EINH2N_R2040 \
    --scenarios EINHSN_R2040 \
    --scenarios EINNPY_R2040 \
    --scenarios EINSSN_R2040 \
    --scenarios EINTPN_R2040 \
    --scenarios ELNDCN_R2040 \
    --scenarios ELNHSN_R2040 \
    --scenarios ELNNPY_R2040 \
    --scenarios ELNSSN_R2040 \
    --scenarios EVNDCN_R2040 \
    --scenarios EVNELN_R2040 \
    --scenarios EVNFEN_R2040 \
    --scenarios EVNHSN_R2040 \
    --scenarios EVNNPY_R2040 \
    --scenarios EVNSSN_R2040 \
    --scenarios FEN_R2040 \
    --scenarios FENDCN_R2040 \
    --scenarios FENEIN_R2040 \
    --scenarios FENELN_R2040 \
    --scenarios FENH2N_R2040 \
    --scenarios FENHPN_R2040 \
    --scenarios FENHSN_R2040 \
    --scenarios FENNPY_R2040 \
    --scenarios FENSSN_R2040 \
    --scenarios FENTPN_R2040 \
    --scenarios H2NDCN_R2040 \
    --scenarios H2NELN_R2040 \
    --scenarios H2NHSN_R2040 \
    --scenarios H2NNPY_R2040 \
    --scenarios H2NSSN_R2040 \
    --scenarios HPNDCN_R2040 \
    --scenarios HPNEIN_R2040 \
    --scenarios HPNELN_R2040 \
    --scenarios HPNH2N_R2040 \
    --scenarios HPNHSN_R2040 \
    --scenarios HPNNPY_R2040 \
    --scenarios HPNSSN_R2040 \
    --scenarios HPNTPN_R2040 \
    --scenarios HSNDCN_R2040 \
    --scenarios NPYDCN_R2040 \
    --scenarios NPYHSN_R2040 \
    --scenarios NPYSSN_R2040 \
    --scenarios PVNDCN_R2040 \
    --scenarios PVNEIN_R2040 \
    --scenarios PVNELN_R2040 \
    --scenarios PVNEVN_R2040 \
    --scenarios PVNFEN_R2040 \
    --scenarios PVNH2N_R2040 \
    --scenarios PVNHPN_R2040 \
    --scenarios PVNHSN_R2040 \
    --scenarios PVNNPY_R2040 \
    --scenarios PVNSSN_R2040 \
    --scenarios PVNTPN_R2040 \
    --scenarios SSNDCN_R2040 \
    --scenarios TPNDCN_R2040 \
    --scenarios TPNELN_R2040 \
    --scenarios TPNH2N_R2040 \
    --scenarios TPNHSN_R2040 \
    --scenarios TPNNPY_R2040 \
    --scenarios TPNSSN_R2040 \
    --scenarios base_R2040

pixi run analyse --overwrite combined-costs \
    --scenarios ALLN_R2050 \
    --scenarios ALLNNPY_R2050 \
    --scenarios DCN_R2050 \
    --scenarios EIN_R2050 \
    --scenarios ELN_R2050 \
    --scenarios EVN_R2050 \
    --scenarios EVNEIN_R2050 \
    --scenarios EVNH2N_R2050 \
    --scenarios EVNHPN_R2050 \
    --scenarios EVNTPN_R2050 \
    --scenarios H2N_R2050 \
    --scenarios HPN_R2050 \
    --scenarios HSN_R2050 \
    --scenarios HSNSSN_R2050 \
    --scenarios NPY_R2050 \
    --scenarios SSN_R2050 \
    --scenarios TPN_R2050 \
    --scenarios D100_R2050 \
    --scenarios D25_R2050 \
    --scenarios D25VGN_R2050 \
    --scenarios D50_R2050 \
    --scenarios PVN_R2050 \
    --scenarios EINDCN_R2050 \
    --scenarios EINELN_R2050 \
    --scenarios EINH2N_R2050 \
    --scenarios EINHSN_R2050 \
    --scenarios EINNPY_R2050 \
    --scenarios EINSSN_R2050 \
    --scenarios EINTPN_R2050 \
    --scenarios ELNDCN_R2050 \
    --scenarios ELNHSN_R2050 \
    --scenarios ELNNPY_R2050 \
    --scenarios ELNSSN_R2050 \
    --scenarios EVNDCN_R2050 \
    --scenarios EVNELN_R2050 \
    --scenarios EVNFEN_R2050 \
    --scenarios EVNHSN_R2050 \
    --scenarios EVNNPY_R2050 \
    --scenarios EVNSSN_R2050 \
    --scenarios FEN_R2050 \
    --scenarios FENDCN_R2050 \
    --scenarios FENEIN_R2050 \
    --scenarios FENELN_R2050 \
    --scenarios FENH2N_R2050 \
    --scenarios FENHPN_R2050 \
    --scenarios FENHSN_R2050 \
    --scenarios FENNPY_R2050 \
    --scenarios FENSSN_R2050 \
    --scenarios FENTPN_R2050 \
    --scenarios H2NDCN_R2050 \
    --scenarios H2NELN_R2050 \
    --scenarios H2NHSN_R2050 \
    --scenarios H2NNPY_R2050 \
    --scenarios H2NSSN_R2050 \
    --scenarios HPNDCN_R2050 \
    --scenarios HPNEIN_R2050 \
    --scenarios HPNELN_R2050 \
    --scenarios HPNH2N_R2050 \
    --scenarios HPNHSN_R2050 \
    --scenarios HPNNPY_R2050 \
    --scenarios HPNSSN_R2050 \
    --scenarios HPNTPN_R2050 \
    --scenarios HSNDCN_R2050 \
    --scenarios NPYDCN_R2050 \
    --scenarios NPYHSN_R2050 \
    --scenarios NPYSSN_R2050 \
    --scenarios PVNDCN_R2050 \
    --scenarios PVNEIN_R2050 \
    --scenarios PVNELN_R2050 \
    --scenarios PVNEVN_R2050 \
    --scenarios PVNFEN_R2050 \
    --scenarios PVNH2N_R2050 \
    --scenarios PVNHPN_R2050 \
    --scenarios PVNHSN_R2050 \
    --scenarios PVNNPY_R2050 \
    --scenarios PVNSSN_R2050 \
    --scenarios PVNTPN_R2050 \
    --scenarios SSNDCN_R2050 \
    --scenarios TPNDCN_R2050 \
    --scenarios TPNELN_R2050 \
    --scenarios TPNH2N_R2050 \
    --scenarios TPNHSN_R2050 \
    --scenarios TPNNPY_R2050 \
    --scenarios TPNSSN_R2050 \
    --scenarios base_R2050

pixi run python scripts/postprocessing/estimate_flexibility_needs.py \
    --output-dir build_postprocess_COMBSC \
    --scenarios ALLN_R2030 \
    --scenarios ALLNNPY_R2030 \
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
