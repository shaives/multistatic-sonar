#!/bin/sh
#SBATCH --array=0-4
#SBATCH --job-name multistatic-sonar
#SBATCH --nodes=1 --tasks-per-node=16 --mem=32GB
#SBATCH --output=outputs/%j_%a_out.txt
#SBATCH --time 0-24:00:00
#SBATCH --mail-user conrad.urban.gy@nps.edu
#SBATCH --mail-type END 


. /etc/profile
source /smallwork/$USER/myenv1/bin/activate

cd multistatic-sonar

ARGS=(Agadir EnglishChannel MontereyPeninsular OpenSeaBiscaya OpenSeaBiscaya2)

python bison.py ${ARGS[$SLURM_ARRAY_TASK_ID]}