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

python scripts/postprocessing/estimate_flexibility_needs.py --output-dir build_postprocess_COMBSC --scenarios EVNEIN_R2050 \
    --scenarios HPNTPNEIN_R2050 \
    --scenarios H2NTPNEIN_R2050 \
    --scenarios H2NHPNEIN_R2050 \
    --scenarios EVNTPN_R2050 \
    --scenarios EVNHPN_R2050 \
    --scenarios EVNH2N_R2050

python scripts/postprocessing/plot_flexibility_needs.py --output-dir build_postprocess_COMBSC

# cd scripts/Balmorel
# for scenario in base_WY1993 \
#     base_WY2020 \
#     base_WY2017 \
#     base_WY2016 \
#     base_WY2015 \
#     base_WY2013 \
#     base_WY2012 \
#     base_WY2011 \
#     base_WY2010 \
#     base_WY2009 \
#     base_WY2007 \
#     base_WY2008 \
#     base_WY2006 \
#     base_WY2005 \
#     base_WY2004 \
#     base_WY2003 \
#     base_WY2002 \
#     base_WY2001 \
#     base_WY1999 \
#     base_WY1997 \
#     base_WY1996 \
#     base_WY1995 \
#     base_WY1982 \
#     base_WY1983 \
#     base_WY1985 \
#     base_WY1989 \
#     base_WY1990 \
#     base_WY1992 \
#     base_WY1994 \
#     base_WY1986 \
#     base_WY1988 \
#     base_WY1991 \
#     base_WY1984 \
#     base_WY1987 \
#     base_WY2014 \
#     base_WY1998 \
#     base_WY2000 \
#     base_WY2018 \
#     base_WY2019; do
#     for runtype in R2050; do
#         # This will fail if the scenario name is incorrect, e.g. if it's named after the scenario folder instead of MainResults suffix!
#         year=$(echo $runtype | tail -c 5)
#         echo "Plotting year ${year} for run ${scenario}_${runtype}.."
#         # python analysis/analyse.py combine-costs
#         # generate_plots "${scenario}_${runtype}" $year
#         #
#         # # Remove old collected pdf to ensure no corruption errors in next colleciton
#         # collected_pdf=analysis/plots/collected_plots_${scenario}_${runtype}.pdf
#         # if [[ -f "$collected_pdf" ]]; then
#         #     rm analysis/plots/collected_plots_${scenario}_${runtype}.pdf
#         # fi
#         # pdfunite analysis/plots/*${scenario}_${runtype}.pdf $collected_pdf
#     done
# done

# python analysis/analyse.py --overwrite combined-costs --scenarios base_WY1993_R2050 \
#     --scenarios base_WY2020_R2050 \
#     --scenarios base_WY2017_R2050 \
#     --scenarios base_WY2016_R2050 \
#     --scenarios base_WY2015_R2050 \
#     --scenarios base_WY2013_R2050 \
#     --scenarios base_WY2012_R2050 \
#     --scenarios base_WY2011_R2050 \
#     --scenarios base_WY2010_R2050 \
#     --scenarios base_WY2009_R2050 \
#     --scenarios base_WY2007_R2050 \
#     --scenarios base_WY2008_R2050 \
#     --scenarios base_WY2006_R2050 \
#     --scenarios base_WY2005_R2050 \
#     --scenarios base_WY2004_R2050 \
#     --scenarios base_WY2003_R2050 \
#     --scenarios base_WY2002_R2050 \
#     --scenarios base_WY2001_R2050 \
#     --scenarios base_WY1999_R2050 \
#     --scenarios base_WY1997_R2050 \
#     --scenarios base_WY1996_R2050 \
#     --scenarios base_WY1995_R2050 \
#     --scenarios base_WY1982_R2050 \
#     --scenarios base_WY1983_R2050 \
#     --scenarios base_WY1985_R2050 \
#     --scenarios base_WY1989_R2050 \
#     --scenarios base_WY1990_R2050 \
#     --scenarios base_WY1992_R2050 \
#     --scenarios base_WY1994_R2050 \
#     --scenarios base_WY1986_R2050 \
#     --scenarios base_WY1988_R2050 \
#     --scenarios base_WY1991_R2050 \
#     --scenarios base_WY1984_R2050 \
#     --scenarios base_WY1987_R2050 \
#     --scenarios base_WY2014_R2050 \
#     --scenarios base_WY1998_R2050 \
#     --scenarios base_WY2000_R2050 \
#     --scenarios base_WY2018_R2050 \
#     --scenarios base_WY2019_R2050
