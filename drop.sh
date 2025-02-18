#!/bin/sh
#SBATCH --job-name bison_256
#SBATCH --nodes=1                               # How many nodes do you want to use? You probably want 1.
#SBATCH --ntasks=1                              # How many tasks (i.e. processors w/ distributed memory) do you want? You probably want 1 here unless using MPI.
#SBATCH --cpus-per-task=32                      # How many cores (i.e. threads w/ shared memory) per processor do you want?
#SBATCH --mem=256GB                              # How much memory do you want total? (You can use suffixes: M=MB, G=GB, T=TB.)
#SBATCH --gres=gpu:0                            # Make sure that you do not request a GPU if you do not use an appropriate partition.
#SBATCH --output=logs/%j_out.txt                # path for logs
#SBATCH --error=logs/%j_error.txt               # path for errors
#SBATCH --time 1-00:00:00                       # max time running on HPC days-hours:minutes:secounds
#SBATCH --mail-user conrad.urban.gy@nps.edu
#SBATCH --mail-type ALL                         # Send email on job start, end, and fail

# Print job parameters to log file
echo "Job Parameters:"
echo "===============================
Job name: $SLURM_JOB_NAME
Job ID: $SLURM_JOB_ID
Submitted from: $SLURM_SUBMIT_HOST
Running on node: $SLURM_NODELIST
Number of nodes: $SLURM_NNODES
Number of tasks: $SLURM_NTASKS
CPUs per task: $SLURM_CPUS_PER_TASK
Memory allocated: $(($SLURM_MEM_PER_NODE/1024))GB
Start time: $(date)
===============================
"

. /etc/profile
source /smallwork/$USER/myenv1/bin/activate

python bison.py MontereyPeninsular_0_new