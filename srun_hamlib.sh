#!/bin/sh

# Execute with MPI the HamLib benchmark using the given number of GPUs and qubit range

NUM_GPUS=$1
MIN=$2
MAX=$3

# this requires NUM_GPUS gpus

echo `date`: Executing HamLib Benchmark on $NUM_GPUS GPUs ...

# pushd hamlib

#appargs=(-a cudaq -c 1 -s 1000 -min $MIN -max $MAX -k 2 -obs -g SpinOperator -ham condensedmatter/tfim/tfim -params 1D-grid:pbc,_h:2)
appargs=(-a cudaq -c 1 -s 1000 -min $MIN -max $MAX -k 1 -obs -g SpinOperator )

echo srun -n $1 python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" 

srun -n $1 python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" 2>&1 | tee hamlib.log

 
