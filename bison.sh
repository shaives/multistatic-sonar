#!/bin/sh
#SBATCH --job-name multistatic-sonar
#SBATCH --nodes=1 
#SBATCH --ntasks=1                              # How many tasks (i.e. processors w/ distributed memory) do you want? You probably want 1 here unless using MPI.
#SBATCH --cpus-per-task=16                      # How many cores (i.e. threads w/ shared memory) per processor do you want?
#SBATCH --mem=64GB
#SBATCH --partition=0                           # partitions = {"0":'primary', "1":'beards', "2":'dsag', "3":'bassett'}
#SBATCH --gres=gpu:0                            # Make sure that you do not request a GPU if you do not use an appropriate partition.
#SBATCH --output=logs/%j_out.txt
#SBATCH --time 1-00:00:00
#SBATCH --mail-user conrad.urban.gy@nps.edu
#SBATCH --mail-type END 


. /etc/profile
source /smallwork/$USER/myenv1/bin/activate

ARGS=(Agadir EnglishChannel MontereyPeninsular OpenSeaBiscaya OpenSeaBiscaya2)

python bison.py ${ARGS[$SLURM_ARRAY_TASK_ID]}