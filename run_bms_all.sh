#!/bin/bash

# Default GPU sizes (powers of 2)
DEFAULT_SIZES="1,2,4,8,16,32,64"

# Parse arguments
ACCOUNT_ARG=""
GPU_SPEC=""
OPTIND=1  # Reset getopts index (needed if script is sourced)

while getopts "A:g:" opt; do
  case $opt in
    A) ACCOUNT_ARG="-A $OPTARG" ;;
    g) GPU_SPEC="$OPTARG" ;;
    *) echo "Usage: $0 [-A account] [-g gpu_sizes]"
       echo ""
       echo "Options:"
       echo "  -A account    NERSC project account (optional)"
       echo "  -g gpu_sizes  GPU sizes to run (optional, default: $DEFAULT_SIZES)"
       echo ""
       echo "GPU sizes can be specified as:"
       echo "  - Comma-separated list: -g 2,8,64"
       echo "  - Range (powers of 2):  -g 4:32  (runs 4,8,16,32)"
       echo "  - Single value:         -g 16"
       exit 1 ;;
  esac
done

# Determine GPU sizes to use
if [ -z "$GPU_SPEC" ]; then
  # Use default
  GPU_SIZES="$DEFAULT_SIZES"
elif echo "$GPU_SPEC" | grep -q ':'; then
  # Range specified (e.g., 4:32)
  MIN_G=$(echo "$GPU_SPEC" | cut -d: -f1)
  MAX_G=$(echo "$GPU_SPEC" | cut -d: -f2)
  GPU_SIZES=""
  G=$MIN_G
  while [ $G -le $MAX_G ]; do
    [ -n "$GPU_SIZES" ] && GPU_SIZES="$GPU_SIZES,"
    GPU_SIZES="$GPU_SIZES$G"
    G=$((G * 2))
  done
else
  # List or single value specified
  GPU_SIZES="$GPU_SPEC"
fi

echo "Running benchmarks with GPU sizes: $GPU_SIZES"
[ -n "$ACCOUNT_ARG" ] && echo "Using account: $ACCOUNT_ARG"

# Submit jobs for each GPU size (convert commas to spaces for iteration)
for G in ${GPU_SIZES//,/ }; do
  echo "sbatch -G $G $ACCOUNT_ARG run_bms.sh"
  sbatch -G $G $ACCOUNT_ARG run_bms.sh
done
