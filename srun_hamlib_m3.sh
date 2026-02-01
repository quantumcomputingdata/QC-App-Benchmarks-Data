#!/bin/sh

# Execute with MPI the HamLib benchmark method 3 using the given number of GPUs and qubit range

NUM_GPUS=$1
MIN=$2
MAX=$3

# this requires NUM_GPUS gpus

echo `date`: Executing HamLib Benchmark method 3 on $NUM_GPUS GPUs ...

# pushd hamlib

# use method 3 for fidelity measure
#appargs=(-a cudaq -c 2 -w -s 1000 -min $MIN -max $MAX -k 2 -m 3 -ham condensedmatter/tfim/tfim -params 1D-grid:pbc,_h:2)
appargs=(-a cudaq -c 2 -w -s 1000 -min $MIN -max $MAX -k 1 -m 3 -steps 10)

echo srun -n $1 python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" 

srun -n $1 python -m mpi4py -m hamlib.hamlib_simulation_benchmark "${appargs[@]}" 2>&1 | tee hamlib_m3.log

 
