#!/bin/bash
#$ -cwd
#$ -m abe
#$ -N output_vis
#$ -M zhang.m.f4b9@m.isct.ac.jp
#$ -l h_rt=00:03:00
#$ -l cpu_40=1

set -eou pipefail
module load intel intel-mpi
module load miniconda >& /dev/null
eval "$(/apps/t4/rhel9/free/miniconda/24.1.2/bin/conda shell.bash hook)" 
set +u
conda activate /gs/bs/tga-guc-lab/dependencies/dependencies_intel/conda/envs/guconda
set -u
python dust_output_vis.py
# python rain_output_vis.py
