#!/bin/bash

sbatch -G 1 run_bms.sh
sbatch -G 2 run_bms.sh
sbatch -G 4 run_bms.sh
sbatch -G 8 run_bms.sh
sbatch -G 16 run_bms.sh
sbatch -G 32 run_bms.sh
sbatch -G 64 run_bms.sh
#sbatch -G 128 run_bms.sh
#sbatch -G 256 run_bms.sh
