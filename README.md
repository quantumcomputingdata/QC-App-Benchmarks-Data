# QC-App-Oriented-Benchmarks Workspace and Data Repository

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

**NOTE:** The **qhpctools** README contains a "cheat sheet" for commands commonly used when working with HPC systems and SLURM.

## Setting up the environment

When executing the QED-C benchmarks or other related project code, we make use of Qiskit, CUDA-Q, and MPI. The instructions here assume you are familiar with setting up a Python environment on a Linux OS.

In your .bashrc file (which is executed on login and at the start of a SLURM job), be sure to include these modules:
```
module load openmpi
module load python/3.12
```
Qiskit and CUDA-Q should be available as pip packages as usual.
```
pip install qiskit
pip install cudaq
... along with any other packages required by the benchmarks or your custom code.
```

**NOTE:** The documentation here describes the current set of scripts that have been used for generating datasets from the QED-C benchmarks on GPU systems. The scripts will eveolve as the projects that use them evolve. For now, they can be thought of as starting points for user customization.

**NOTE:** The **srun** scripts below use the default NERSC account id associated with your username. They do not currently provide a way to pass a different NERSC account id.  Executing code in a different project is available only when using the **run_bms.sh** script below.

### Single-GPU Execution

Go to the top level of this repo.

To run any single benchmark on just one GPU, invoke the benchmark as a module and specify the CUDA-Q API.
```
python -m hidden_shift.hs_benchmark -a cudaq
```

### Multi-GPU Execution

To execute the benchmarks on multiple GPUs using the mgpu aggregation of state across the GPUs, first allocate the number of GPUs on which you would like to run. The following command allocates 4 GPUs and logs you into the first of these, from where you can run multi-GPU experiments. (see the qhpctools doc for more options)
```
alloc_gpus.sh -G 4
```
Once connected to the GPUs, use the **srun** command to execute any of the benchmark programs (shown here for 4 GPUs):
```
srun -n 4 python -m mpi4py -m hidden_shift.hs_benchmark -a cudaq    # {add'l args, e.g. -n 4}
```
The default behavior of the benchmarks is to execute over a range of qubit widths, from 2 to 8 qubits. You can modify the range and other parameters using the arguments presented using the --help argument to the benchmark program. For convenience, the **srun_bm.sh** script is provided to easily control the number of GPUs to use and the range of qubit widths.  Pass the NUM_GPUS, MIN, MAX args follwed by the BMDIR and BMNAME, e.g
```
source srun_bm.sh 4 25 26 quantum_fourier_transform qft_benchmark
```
We provide two additional scripts for running the **hamlib** benchmark, which is treated as a special case, since it has several app-specific arguments.
```
source srun_hamlib.sh 4 25 26         # use observable method
source srun_hamlib_m3.sh 4 25 26      # use method 3 for fidelity check
```

### HamLib Comprehensive Testing

The **run_hamlib_test.sh** script executes the HamLib benchmark in four different execution modes for a given Hamiltonian, allowing comparison of parallelization strategies:

1. **SpinOperator, Single GPU** - Baseline using CUDA-Q native `observe()`
2. **simple, Single GPU** - Baseline using Pauli term sampling
3. **SpinOperator, mgpu mode** - State vector distributed across GPUs
4. **simple, -pm mpi** - Parallel circuit execution across GPUs

```bash
# Usage: run_hamlib_test.sh NUM_GPUS MIN_QUBITS MAX_QUBITS [additional args]
source run_hamlib_test.sh 16 20 28 -ham condensedmatter/tfim/tfim -params 1D-grid:pbc,h:2
```

The **run_hamlib_tests_3.sh** script runs `run_hamlib_test.sh` across three representative Hamiltonians:
- TFIM (Transverse Field Ising Model) - simple structure, 2 circuit groups
- Bose-Hubbard - intermediate complexity, 9-11 circuit groups
- H2 (Hydrogen) - chemistry Hamiltonian, many circuit groups

```bash
# Usage: run_hamlib_tests_3.sh NUM_GPUS [additional args]
source run_hamlib_tests_3.sh 16
```

Data from these tests are stored in `__data/nvidia_g{N}/` directories, with separate JSON files per Hamiltonian.

### Run All Benchmarks from One Script and Sweep Available Qubit Widths

The **run_bms.sh** script is provided for convenience.  It sweeps over a range of qubit widths that is calculated to maximize the avaiable memory across the available GPUs and executes a set of several representative  benchmarks.  Note this script can take a long time, possibly minutes. You can comment out parts if you would like to reduce the range of qubit widths or benchmarks executed.
This script determines the number of available GPUs from the **SLURM_GPUS** environment variable and requires no other arguments, as the sweep range is calculated based on this value.
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

Data are stored in the **__data** directory and images are stored in the **__images** directory.

### Data Directory Structure

```
__data/
├── nvidia_g1/                           # HamLib data for 1 GPU
│   └── HamLib-obs-{hamiltonian}.json
├── nvidia_g4/                           # HamLib data for 4 GPUs
├── nvidia_g8/                           # HamLib data for 8 GPUs
├── nvidia_g16/                          # HamLib data for 16 GPUs
├── DATA-nvidia-1g-1.json                # QED-C benchmark data for 1 GPU
├── DATA-nvidia-16g-1.json               # QED-C benchmark data for 16 GPUs
└── Perlmutter-80GB-260310/              # Archived dataset (example)
    ├── nvidia_g1/
    ├── nvidia_g16/
    └── DATA-nvidia-*g-1.json
```

## Visualization

Two plotting programs are provided for generating publication-ready figures from benchmark data.

### plot_parallel_execution.py

Generates plots for HamLib observable benchmark results, comparing execution modes and GPU scaling.

**Plots generated:**
- Mode comparison: SpinOperator vs simple, 1 GPU vs N GPUs
- GPU scaling: Execution time across 1, 4, 8, 16 GPUs for parallel circuit execution

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--data_dir` | | Base data directory | `__data` |
| `--output_dir` | | Output directory for images | `__images` |
| `--num_gpus` | | GPU count for mode comparison | `16` |
| `--data_suffix` | `-suffix` | Subdirectory for archived data | None |

```bash
# Generate plots from top-level data
python plot_parallel_execution.py

# Generate plots from archived dataset
python plot_parallel_execution.py --data_suffix Perlmutter-80GB-260310
python plot_parallel_execution.py -suffix Perlmutter-80GB-260310
```

**Output files:**
- `parallel_exec_{hamiltonian}.{png,pdf}` - Individual Hamiltonian plots
- `parallel_exec_combined.{png,pdf}` - All Hamiltonians side-by-side
- `gpu_scaling_{hamiltonian}.{png,pdf}` - GPU scaling per Hamiltonian
- `gpu_scaling_combined.{png,pdf}` - GPU scaling combined

### plot_benchmark_scaling.py

Generates plots for QED-C fidelity benchmark results showing GPU scaling.

**Plots generated:**
- Execution time vs qubits with traces for each GPU count (1-256)

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--data_dir` | | Base data directory | `__data` |
| `--output_dir` | | Output directory for images | `__images` |
| `--data_suffix` | `-suffix` | Subdirectory for archived data | None |

```bash
# Generate plots from top-level data
python plot_benchmark_scaling.py

# Generate plots from archived dataset
python plot_benchmark_scaling.py --data_suffix Perlmutter-80GB-260310
python plot_benchmark_scaling.py -suffix Perlmutter-80GB-260310
```

**Output files:**
- `benchmark_scaling_{benchmark}.{png,pdf}` - Individual benchmark plots
- `benchmark_scaling_combined.{png,pdf}` - All benchmarks side-by-side

### Archiving Data

For paper submissions, copy final datasets to a named subdirectory under `__data/`:
```bash
# Create archive with system name, configuration, and date
mkdir __data/Perlmutter-80GB-260310
cp -r __data/nvidia_g* __data/Perlmutter-80GB-260310/
cp __data/DATA-nvidia-*g-1.json __data/Perlmutter-80GB-260310/

# Generate plots from archived data (creates __images/Perlmutter-80GB-260310/)
python plot_parallel_execution.py -suffix Perlmutter-80GB-260310
python plot_benchmark_scaling.py -suffix Perlmutter-80GB-260310
```
