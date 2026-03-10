#!/bin/bash

# Execute the HamLib benchmark using the given number of GPUs and qubit range, in 3 modes

NUM_GPUS=$1
MIN=$2
MAX=$3

# remove first 3 arguments so $@ now contains the extras
shift 3

echo "$(date): Executing HamLib Benchmark on $NUM_GPUS GPUs ..."

# pushd hamlib

appargs=(-a cudaq -c 1 -s 1000 -min $MIN -max $MAX -k 1 --time 0.1 -obs -m 4 $@)

#echo srun -n $NUM_GPUS python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" 

# ************ no MPI ************************

# run using single GPU, without MPI, using SpinOperator
echo "========================================================================="
echo Running hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g SpinOperator on one GPU

python -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g SpinOperator -suffix "_g1" 2>&1 | tee hamlib.log

# run using single GPU, without MPI, using simple commuting groups
echo "========================================================================="
echo Running hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g simple on one GPU

python -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g simple -suffix "_g1" 2>&1 | tee hamlib.log

# ************ using MPI ************************

# run using mgpu mode and MPI, sharing memory across GPUs for more qubits and faster execution, using SpinOperator
echo "========================================================================="
echo Running hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g SpinOperator with MPI Shared GPUs

srun -n $NUM_GPUS python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g SpinOperator -suffix "_g$NUM_GPUS" 2>&1 | tee hamlib.log


# run using parallel execution mode, using MPI, using simple commuting groups
echo "========================================================================="
echo Running hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g simple on MPI parallel GPUs

srun -n $NUM_GPUS python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" -g simple -pm mpi -suffix "_g$NUM_GPUS" 2>&1 | tee hamlib.log

