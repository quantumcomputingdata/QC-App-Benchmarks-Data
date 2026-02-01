#!/bin/bash
#SBATCH -G 1
#SBATCH -C gpu&hbm80g
#SBATCH -q regular
#SBATCH -t 00:15:00
#SBATCH -J my_batch_bms
#SBATCH -o slurm-%j.out
#SBATCH --mail-type=END,FAIL
# (omitting --mail-user uses your NERSC account email)

# SLURM_GPUS will contain the actual number allocated
# (either the default from #SBATCH -G 4, or what you override with -G on command line)
TOTAL_GPUS=${SLURM_GPUS}
JOB_ID=${SLURM_JOB_ID}

if [ -z "$TOTAL_GPUS" ]; then
    TOTAL_GPUS=1
fi

echo "Job ID: $JOB_ID - Running with $TOTAL_GPUS GPUs"

export QEDCBMS_DATA_SUFFIX="-"$TOTAL_GPUS"g-1"
echo QEDCBMS_DATA_SUFFIX=$QEDCBMS_DATA_SUFFIX

#nvidia-smi --loop=1 > gpu_log.txt &
#GPULOG_PID=$!
#echo $GPULOG_PID

# make sure MPI is loaded
module load openmpi

# this is slow, omit for now
# echo "CUDAQ version: $(python -c 'import cudaq; print(cudaq.__version__)')"
# echo "QISKIT version: $(python -c 'import qiskit; print(qiskit.__version__)')"

# echo `printenv | grep FABRIC`
# echo `printenv | grep CUDAQ`

# set this for better network performance with MPI
export CUDAQ_GPU_FABRIC=NVL
#export UBACKEND_USE_FABRIC_HANDLE=0

# This is a patch for a possible issue with CUDA-Q 0.12 setting up network connectivity
# The second value in the pair is specific to the number of GPUs used 
# export CUDAQ_GLOBAL_INDEX_BITS="2,4"   # (for 64 gpus)
# Compute the second value in pair using log2
if [ $TOTAL_GPUS -ge 8 ]; then
    QUARTER=$((TOTAL_GPUS / 4))
    SECOND_NUM=0
    temp=$QUARTER
    while [ $temp -gt 1 ]; do
        temp=$((temp / 2))
        SECOND_NUM=$((SECOND_NUM + 1))
    done
    export CUDAQ_GLOBAL_INDEX_BITS="2,$SECOND_NUM"
else
    unset CUDAQ_GLOBAL_INDEX_BITS
fi

echo `printenv | grep FABRIC`
echo `printenv | grep CUDAQ`

declare -A qubit_range=(
    [1]="26:33"
    [2]="26:34"
    [4]="25:35"
    [8]="26:36"
    [16]="26:37"
    [32]="26:38"
    [64]="26:39"
    [128]="26:40"
    [256]="26:41"
)

declare -A qubit_range_h=(
    [1]="26:32"
    [2]="26:32"
    [4]="26:34"
    [8]="26:34"
    [16]="26:36"
    [32]="26:36"
    [64]="26:38"
    [128]="26:38"
    [256]="26:40"
)

IFS=':' read -r MIN MAX <<< "${qubit_range[$TOTAL_GPUS]:-28:32}"
IFS=':' read -r HMIN HMAX <<< "${qubit_range_h[$TOTAL_GPUS]:-28:32}"

echo "Range of Qubits: $MIN $MAX"

# clear this, just in case
unset CUDAQ_MAX_GPU_MEMORY_GB

############################
# Run the benchmark programs

./srun_bm.sh $TOTAL_GPUS $MIN $MAX hidden_shift hs_benchmark

./srun_bm.sh $TOTAL_GPUS $MIN $MAX quantum_fourier_transform qft_benchmark

./srun_bm.sh $TOTAL_GPUS $MIN $MAX phase_estimation pe_benchmark

#./srun_qpe.sh $TOTAL_GPUS $MIN $MAX

#./srun_hamlib_m3.sh $TOTAL_GPUS $MIN $MAX

# HamLib benchmark requires this max memory limit, otherwise it overflows 80GB
# The estimate_expectation() function requires twice the memory
export CUDAQ_MAX_GPU_MEMORY_GB=40

#./srun_hamlib.sh $TOTAL_GPUS $HMIN $HMAX

####################
# Clean up variables

unset CUDAQ_MAX_GPU_MEMORY_GB

#kill $GPULOG_PID

