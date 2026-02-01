#!/bin/bash

# Parse optional -A argument
ACCOUNT_ARG=""
while getopts "A:" opt; do
  case $opt in
    A) ACCOUNT_ARG="-A $OPTARG" ;;
    *) echo "Usage: $0 [-A account]" >&2; exit 1 ;;
  esac
done

sbatch -G 1 $ACCOUNT_ARG run_bms.sh
sbatch -G 2 $ACCOUNT_ARG run_bms.sh
sbatch -G 4 $ACCOUNT_ARG run_bms.sh
sbatch -G 8 $ACCOUNT_ARG run_bms.sh
sbatch -G 16 $ACCOUNT_ARG run_bms.sh
sbatch -G 32 $ACCOUNT_ARG run_bms.sh
sbatch -G 64 $ACCOUNT_ARG run_bms.sh
#sbatch -G 128 $ACCOUNT_ARG run_bms.sh
#sbatch -G 256 $ACCOUNT_ARG run_bms.sh
