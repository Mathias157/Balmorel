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

python scripts/postprocessing/estimate_flexibility_needs.py \
    --output-dir build_postprocess_WY \
    --overwrite-cache \
    --scenarios base_WY1982_R2050 \
    --scenarios base_WY1983_R2050 \
    --scenarios base_WY1984_R2050 \
    --scenarios base_WY1985_R2050 \
    --scenarios base_WY1986_R2050 \
    --scenarios base_WY1987_R2050 \
    --scenarios base_WY1988_R2050 \
    --scenarios base_WY1989_R2050 \
    --scenarios base_WY1990_R2050 \
    --scenarios base_WY1991_R2050 \
    --scenarios base_WY1992_R2050 \
    --scenarios base_WY1993_R2050 \
    --scenarios base_WY1994_R2050 \
    --scenarios base_WY1995_R2050 \
    --scenarios base_WY1996_R2050 \
    --scenarios base_WY1997_R2050 \
    --scenarios base_WY1998_R2050 \
    --scenarios base_WY1999_R2050 \
    --scenarios base_WY2000_R2050 \
    --scenarios base_WY2001_R2050 \
    --scenarios base_WY2002_R2050 \
    --scenarios base_WY2003_R2050 \
    --scenarios base_WY2004_R2050 \
    --scenarios base_WY2005_R2050 \
    --scenarios base_WY2006_R2050 \
    --scenarios base_WY2007_R2050 \
    --scenarios base_WY2008_R2050 \
    --scenarios base_WY2009_R2050 \
    --scenarios base_WY2010_R2050 \
    --scenarios base_WY2011_R2050 \
    --scenarios base_WY2012_R2050 \
    --scenarios base_WY2013_R2050 \
    --scenarios base_WY2014_R2050 \
    --scenarios base_WY2015_R2050 \
    --scenarios base_WY2016_R2050 \
    --scenarios base_WY2017_R2050 \
    --scenarios base_WY2018_R2050 \
    --scenarios base_WY2019_R2050 \
    --scenarios base_WY2020_R2050
