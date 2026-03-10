#!/bin/bash

# Execute the HamLib benchmark test against 3 different Hamiltonians

NUM_GPUS=$1

# remove first 1 arguments so $@ now contains the extras
shift 1

echo "$(date): Executing HamLib Benchmark on multiple Hamiltonians using $NUM_GPUS GPUs ..."

source run_hamlib_test.sh $NUM_GPUS 20 28 -ham condensedmatter/bosehubbard/BH_D-1_d-4 -params 1D-grid:nonpbc,enc:gray,U:10 $@

source run_hamlib_test.sh $NUM_GPUS 20 28 -ham condensedmatter/tfim/tfim -params 1D-grid:pbc,h:2 $@

source run_hamlib_test.sh $NUM_GPUS 8 20 -ham chemistry/electronic/standard/H2 -params "ham_BK:" $@

