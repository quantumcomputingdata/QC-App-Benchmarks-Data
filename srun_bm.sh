#!/bin/sh

# Execute with MPI the specified benchmark using the given number of GPUs and qubit range

NUM_GPUS=$1
MIN=$2
MAX=$3
BMDIR=$4
BMNAME=$5

# this requires NUM_GPUS gpus

echo `date`: Executing $BMDIR Benchmark on $NUM_GPUS GPUs ...

#pushd $BMDIR

appargs=(-a cudaq -c 2 -w -s 1000 -min $MIN -max $MAX)

echo srun -n $NUM_GPUS python -m mpi4py -m $BMDIR.$BMNAME "${appargs[@]}" 

srun -n $NUM_GPUS python -m mpi4py -m $BMDIR.$BMNAME "${appargs[@]}" 2>&1 | tee $BMNAME.log
