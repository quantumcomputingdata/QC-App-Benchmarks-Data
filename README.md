# QC-App-Oriented-Benchmarks Data Repository

This repository contains assorted scripts, notebooks, and programs useful for executing the QED-C Application-Oriented Benchmarks on various quantum computing systems.

## Configuration

At the top level of your working directory, clone this repository.
```
cd $HOME
git clone https://github.com/quantumcomputingdata/QC-App-Benchmarks-Data.git
```
The scripts that are used to execute the benchmarks in a GPU environment with CUDA-Q are all currently available at the top level of the repo. 
Note that this will likely change as this workspace evolves.

This repo depends on the QED-C benchmark repo also being available (possibly in parallel) and having had a pip install done on it.
Currently, this is done by cloing the QED-C repo somewhere and installing this way (since the QED-C is not yet released to pypy):
```
cd $HOME
git clone https://github.com/SRI-International/QC-App-Oriented-Benchmarks.git
cd QC-App-Oriented-Benchmarks
pip install -e .
```
Lastly, there is available another repository called **qhpctools** which provides some generaly useful HPC tools that are not specific to running benchmark programs.
At the top level of your workspace, clone that repository and add the bin folder to your path (most likely added in your .bashrc file):
```
cd $HOME
git clone https://github.com/quantumcomputingdata/qhpctools.git
export PATH="$HOME/apps/qhpctools/bin:$HOME/bin"
```

**TODO:** Need to describe here how to setup the python and cudea environments.

## Running Benchmarks on CUDA-Q

**NOTE:** The documentation here describes the current set of scripts that have been used for generating datasets from the QED-C benchmarks on GPU systems. The scripts will eveolve as the projects that use them evolve. For now, they can be thought of as starting points for user customization.

**NOTE:** The **srun** scripts below use the default NERSC account id associated with your username. They do not currently provide a way to pass a different NERSC account id.  This is available only when using the **run_bms.sh** script below.

### Single-GPU Execution

Go to the top level of this repo.

To run any single benchmark on just one GPU, invoke the benchmark as a module and specify the CUDA-Q API.
```
python -m hidden_shift.hs_benchmark -a cudaq
```

### Multi-GPU Execution

To execute the benchmarks on multiple GPUs using the mgpu aggregation of state across the GPUs, use the **srun** command (shown here for 4 GPUs):
```
srun -n 4 python -m mpi4py -m hidden_shift.hs_benchmark -a cudaq    # {add'l args, e.g. -n 4}
```
The **srun_bm.sh** script is provided to make this more convenient.  Pass the NUM_GPUS, MIN, MAX args follwed by the BMDIR and BMNAME, e.g
```
source srun_bm.sh 4 25 26 quantum_fourier_transform qft_benchmark
```
We also have two scripts for running hamlib wihc is tread as a special case since it has some spp-specific arguments. 
```
source srun_hamlib.sh 4 25 26         # use observable method
source srun_hamlib_m3.sh 4 25 26      # use method 3 for fidelity check
```

### Run All Benchmarks from One Script and Sweep Available Qubit Widths

The **run_bms.sh** script is provided for convenience.  It sweeps over a selected range of qubit widths that will maximize the avaiable memory across the given mumber of GPUs and executes the available benchmarks.  Note this script can take a long time. You can comment out parts if you would like to reduce the range of execution.
This script determines the number of available GPUs from the **SLURM_GPUS** env variable and requires no other arguments, as the sweep range is hardcoded.
```
run_bms.sh
```
If executed with **sbatch**, the number of GPUs can be specified with the -G argument.
```
sbatch -G 4 run_bms.sh
```
You can also optionally specify the NERSC account id to use as well as a non-default email address to which to send notifications of completion.
```
sbatch -G 4 -A mNNNN --mail-user otheremail@emailservice.com run_bms.sh
```

> **Note:** When running sbatch without the `-A` option, GPU allocations may be limited to 16 GPUs. To run with more than 16 GPUs, always specify your NERSC account explicitly with `-A`.

### Run All Benchmarks across a Range of GPU Counts

The **run_bms_all.sh** script can be used to run all the benchmarks defined in **run_bms.sh**, submitting separate jobs for multiple GPU counts.

| Argument | Description | Default |
|----------|-------------|---------|
| `-A account` | NERSC project account | User's default |
| `-g gpu_sizes` | GPU sizes to run | 1,2,4,8,16,32,64 |

The `-g` option accepts:
- **Comma-separated list:** `-g 2,8,64`
- **Range (powers of 2):** `-g 4:32` (runs 4,8,16,32)
- **Single value:** `-g 16`

Examples:
```bash
# Run with default GPU sizes (1,2,4,8,16,32,64)
./run_bms_all.sh

# Run with specific account
./run_bms_all.sh -A m1234

# Run only specific GPU sizes
./run_bms_all.sh -g 4,16,64

# Run a range of GPU sizes (powers of 2 from 4 to 32)
./run_bms_all.sh -g 4:32

# Run single GPU size with specific account
./run_bms_all.sh -A m1234 -g 8
```

### WORK-IN-PROGRESS - RCS benchmark

At the top-level, there is currently checked in the rcs.py file, which contains a simple random circuit sampling test, specifically for CUDA-Q.  The **run_rcs_tests.sh** script executes this with two different configurations. This may be instantiated as a new benchmark within the QED-C repo, but for now it is a work in progress.

## Data Collection

Data are stored in **_data** directory and images stored in **__images** with an appendage that indicates the number of GPUs on which the results were obtained.
