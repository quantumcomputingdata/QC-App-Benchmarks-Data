"""
Plot Parallel Execution Results for HamLib Benchmarks

Reads JSON data files from nvidia_g* directories and creates plots:

1. Mode comparison (original): Compare execution modes at fixed GPU count
   - 4 traces per Hamiltonian: SpinOperator/simple x 1GPU/N-GPUs

2. GPU scaling (new): Show performance improvement as GPU count increases
   - For the -pm mpi case (simple group_method)
   - One trace per GPU count (1, 4, 8, 16)

Usage:
    python plot_parallel_execution.py [--data_dir PATH] [--output_dir PATH] [--num_gpus N]
"""

import json
import os
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


# Display name mappings for known Hamiltonians (optional, for nicer labels)
# If a Hamiltonian ID is not in this dict, the ID itself will be used as the label
HAMILTONIAN_NAMES = {
    "condensedmatter_tfim_tfim": "TFIM (Transverse Field Ising Model)",
    "condensedmatter_bosehubbard_BH_D-1_d-4": "Bose-Hubbard",
    "chemistry_electronic_standard_H2": "H2 (Hydrogen)",
}

# Preferred ordering for Hamiltonians (simpler to more complex)
# Hamiltonians not in this list will appear at the end, sorted alphabetically
HAMILTONIAN_ORDER = [
    "condensedmatter_tfim_tfim",
    "condensedmatter_bosehubbard_BH_D-1_d-4",
    "chemistry_electronic_standard_H2",
]


def discover_hamiltonians(data_dir):
    """
    Scan data directory for HamLib-obs-*.json files and return list of
    (ham_id, display_name) tuples.
    """
    import glob

    hamiltonians = set()

    # Look in all nvidia_g* subdirectories
    for gpu_dir in glob.glob(str(data_dir / "nvidia_g*")):
        for filepath in glob.glob(os.path.join(gpu_dir, "HamLib-obs-*.json")):
            filename = os.path.basename(filepath)
            # Extract ham_id from "HamLib-obs-{ham_id}.json"
            if filename.startswith("HamLib-obs-") and filename.endswith(".json"):
                ham_id = filename[11:-5]  # Remove prefix and suffix
                hamiltonians.add(ham_id)

    # Sort by preferred order, then alphabetically for unknown Hamiltonians
    def sort_key(ham_id):
        if ham_id in HAMILTONIAN_ORDER:
            return (0, HAMILTONIAN_ORDER.index(ham_id))
        return (1, ham_id)

    result = []
    for ham_id in sorted(hamiltonians, key=sort_key):
        display_name = HAMILTONIAN_NAMES.get(ham_id, ham_id)
        result.append((ham_id, display_name))

    return result


def discover_gpu_counts(data_dir):
    """
    Scan data directory for nvidia_g* subdirectories and return sorted list
    of GPU counts.
    """
    import glob
    import re

    gpu_counts = set()

    for gpu_dir in glob.glob(str(data_dir / "nvidia_g*")):
        dirname = os.path.basename(gpu_dir)
        # Extract number from "nvidia_g{N}"
        match = re.match(r'nvidia_g(\d+)$', dirname)
        if match:
            gpu_counts.add(int(match.group(1)))

    return sorted(gpu_counts)


def get_gpu_style(num_gpus, gpu_counts):
    """
    Generate marker, color, and label for a given GPU count.
    Uses a consistent color progression based on position in the list.
    """
    markers = ['o-', 's-', '^-', 'd-', 'v-', '<-', '>-', 'p-', 'h-', '*-']
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(gpu_counts)))

    idx = gpu_counts.index(num_gpus) if num_gpus in gpu_counts else 0
    marker = markers[idx % len(markers)]
    color = colors[idx]
    label = f"{num_gpus} GPU" if num_gpus == 1 else f"{num_gpus} GPUs"

    return marker, color, label


def save_plot(fig, output_dir, basename):
    """
    Save plot to both PNG and PDF formats.
    Returns the PNG filepath.
    """
    png_file = os.path.join(output_dir, f"{basename}.png")
    pdf_file = os.path.join(output_dir, f"{basename}.pdf")

    fig.savefig(png_file, dpi=150, bbox_inches='tight')
    fig.savefig(pdf_file, bbox_inches='tight')

    print(f"  Saved: {png_file}")
    print(f"  Saved: {pdf_file}")

    return png_file


def load_json_data(filepath):
    """Load JSON data from file, return empty list if file doesn't exist."""
    if not os.path.exists(filepath):
        print(f"  Warning: File not found: {filepath}")
        return []
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_time_data(data, group_method):
    """
    Extract qubit sizes and execution times for a specific group_method.

    Returns:
        qubits: list of qubit counts
        times: list of exp_time_computed values
    """
    filtered = [d for d in data if d.get('group_method') == group_method]
    # Sort by qubit count (group field)
    filtered.sort(key=lambda x: x.get('group', 0))

    qubits = [d.get('group') for d in filtered]
    times = [d.get('exp_time_computed') for d in filtered]

    return qubits, times


def create_hamiltonian_plot(ham_id, ham_name, data_1gpu, data_ngpu, num_gpus, output_dir):
    """
    Create a single plot for one Hamiltonian with 4 traces.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Extract data for each configuration
    configs = [
        ("SpinOperator", data_1gpu, "1 GPU", "o-", "tab:blue"),
        ("SpinOperator", data_ngpu, f"{num_gpus} GPUs (mgpu)", "s--", "tab:cyan"),
        ("simple", data_1gpu, "1 GPU", "^-", "tab:orange"),
        ("simple", data_ngpu, f"{num_gpus} GPUs (-pm mpi)", "d--", "tab:red"),
    ]

    has_data = False
    all_qubits = set()

    for group_method, data, label_suffix, marker, color in configs:
        qubits, times = extract_time_data(data, group_method)

        if qubits and times:
            has_data = True
            all_qubits.update(qubits)
            label = f"{group_method}, {label_suffix}"
            ax.plot(qubits, times, marker, label=label, color=color,
                   linewidth=2, markersize=8)

    if not has_data:
        print(f"  No data found for {ham_name}, skipping plot")
        plt.close(fig)
        return None

    # Configure plot
    ax.set_xlabel("Number of Qubits", fontsize=12)
    ax.set_ylabel("Execution Time (seconds)", fontsize=12)
    ax.set_title(f"Parallel Execution Performance: {ham_name}", fontsize=14)
    ax.set_yscale('log')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Set x-ticks to actual qubit values
    if all_qubits:
        sorted_qubits = sorted(all_qubits)
        ax.set_xticks(sorted_qubits)

    plt.tight_layout()

    # Save plot
    output_file = save_plot(fig, output_dir, f"parallel_exec_{ham_id}")

    plt.close(fig)
    return output_file


def create_combined_plot(all_data, num_gpus, output_dir, hamiltonians):
    """
    Create a combined figure with subplots for all Hamiltonians.
    """
    num_hams = len(hamiltonians)
    if num_hams == 0:
        print("  No Hamiltonians to plot")
        return None

    fig, axes = plt.subplots(1, num_hams, figsize=(5.5 * num_hams, 5))
    if num_hams == 1:
        axes = [axes]

    for idx, (ham_id, ham_name) in enumerate(hamiltonians):
        ax = axes[idx]
        data_1gpu, data_ngpu = all_data.get(ham_id, ([], []))

        configs = [
            ("SpinOperator", data_1gpu, "1 GPU", "o-", "tab:blue"),
            ("SpinOperator", data_ngpu, f"{num_gpus} GPUs", "s--", "tab:cyan"),
            ("simple", data_1gpu, "1 GPU", "^-", "tab:orange"),
            ("simple", data_ngpu, f"{num_gpus} GPUs", "d--", "tab:red"),
        ]

        all_qubits = set()

        for group_method, data, label_suffix, marker, color in configs:
            qubits, times = extract_time_data(data, group_method)

            if qubits and times:
                all_qubits.update(qubits)
                label = f"{group_method}, {label_suffix}"
                ax.plot(qubits, times, marker, label=label, color=color,
                       linewidth=2, markersize=6)

        ax.set_xlabel("Qubits", fontsize=11)
        ax.set_ylabel("Time (sec)", fontsize=11)
        ax.set_title(ham_name, fontsize=12)
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)

        if all_qubits:
            sorted_qubits = sorted(all_qubits)
            ax.set_xticks(sorted_qubits)

        # Only show legend on first plot
        if idx == 0:
            ax.legend(loc='upper left', fontsize=8)

    plt.suptitle(f"HamLib Parallel Execution: 1 GPU vs {num_gpus} GPUs", fontsize=14, y=1.02)
    plt.tight_layout()

    output_file = save_plot(fig, output_dir, "parallel_exec_combined")

    plt.close(fig)
    return output_file


def create_gpu_scaling_plot(ham_id, ham_name, gpu_data, output_dir, gpu_counts):
    """
    Create a plot showing GPU scaling for one Hamiltonian.
    Shows execution time vs qubits with one trace per GPU count.
    Uses only 'simple' group_method (the -pm mpi parallel circuit case).
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    has_data = False
    all_qubits = set()

    for num_gpus in gpu_counts:
        data = gpu_data.get(num_gpus, [])
        marker, color, label = get_gpu_style(num_gpus, gpu_counts)

        qubits, times = extract_time_data(data, "simple")

        if qubits and times:
            has_data = True
            all_qubits.update(qubits)
            ax.plot(qubits, times, marker, label=label, color=color,
                   linewidth=2, markersize=8)

    if not has_data:
        print(f"  No data found for {ham_name}, skipping GPU scaling plot")
        plt.close(fig)
        return None

    # Configure plot
    ax.set_xlabel("Number of Qubits", fontsize=12)
    ax.set_ylabel("Execution Time (seconds)", fontsize=12)
    ax.set_title(f"GPU Scaling (-pm mpi): {ham_name}", fontsize=14)
    ax.set_yscale('log')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Set x-ticks to actual qubit values
    if all_qubits:
        sorted_qubits = sorted(all_qubits)
        ax.set_xticks(sorted_qubits)

    plt.tight_layout()

    # Save plot
    output_file = save_plot(fig, output_dir, f"gpu_scaling_{ham_id}")

    plt.close(fig)
    return output_file


def create_gpu_scaling_combined_plot(all_gpu_data, output_dir, hamiltonians, gpu_counts):
    """
    Create a combined figure with GPU scaling subplots for all Hamiltonians.
    """
    num_hams = len(hamiltonians)
    if num_hams == 0:
        print("  No Hamiltonians to plot")
        return None

    fig, axes = plt.subplots(1, num_hams, figsize=(5.5 * num_hams, 5))
    if num_hams == 1:
        axes = [axes]

    for idx, (ham_id, ham_name) in enumerate(hamiltonians):
        ax = axes[idx]
        gpu_data = all_gpu_data.get(ham_id, {})

        all_qubits = set()

        for num_gpus in gpu_counts:
            data = gpu_data.get(num_gpus, [])
            marker, color, label = get_gpu_style(num_gpus, gpu_counts)

            qubits, times = extract_time_data(data, "simple")

            if qubits and times:
                all_qubits.update(qubits)
                ax.plot(qubits, times, marker, label=label, color=color,
                       linewidth=2, markersize=6)

        ax.set_xlabel("Qubits", fontsize=11)
        ax.set_ylabel("Time (sec)", fontsize=11)
        ax.set_title(ham_name, fontsize=12)
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)

        if all_qubits:
            sorted_qubits = sorted(all_qubits)
            ax.set_xticks(sorted_qubits)

        # Only show legend on first plot
        if idx == 0:
            ax.legend(loc='upper left', fontsize=9)

    plt.suptitle("HamLib GPU Scaling: Parallel Circuit Execution (-pm mpi)", fontsize=14, y=1.02)
    plt.tight_layout()

    output_file = save_plot(fig, output_dir, "gpu_scaling_combined")

    plt.close(fig)
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Plot parallel execution results")
    parser.add_argument("--data_dir", type=str, default="__data",
                       help="Base directory containing nvidia_g* subdirectories")
    parser.add_argument("--output_dir", type=str, default="__images",
                       help="Directory to save plot images")
    parser.add_argument("--num_gpus", type=int, default=16,
                       help="Number of GPUs for MPI comparison (default: 16)")

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / args.data_dir
    output_dir = script_dir / args.output_dir

    # Discover Hamiltonians and GPU counts from data files
    hamiltonians = discover_hamiltonians(data_dir)
    if not hamiltonians:
        print(f"No HamLib data files found in {data_dir}/nvidia_g*/")
        return

    gpu_counts = discover_gpu_counts(data_dir)
    if not gpu_counts:
        print(f"No nvidia_g* directories found in {data_dir}/")
        return

    print(f"Discovered {len(hamiltonians)} Hamiltonian(s):")
    for ham_id, ham_name in hamiltonians:
        print(f"  - {ham_name}")
    print(f"\nDiscovered {len(gpu_counts)} GPU configuration(s): {gpu_counts}")
    print()

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Directory names
    dir_1gpu = data_dir / "nvidia_g1"
    dir_ngpu = data_dir / f"nvidia_g{args.num_gpus}"

    print(f"Loading data from:")
    print(f"  1 GPU:        {dir_1gpu}")
    print(f"  {args.num_gpus} GPUs:       {dir_ngpu}")
    print()

    # Load and plot each Hamiltonian (original mode comparison plots)
    all_data = {}

    for ham_id, ham_name in hamiltonians:
        print(f"Processing {ham_name}...")

        # Construct file paths
        filename = f"HamLib-obs-{ham_id}.json"
        file_1gpu = dir_1gpu / filename
        file_ngpu = dir_ngpu / filename

        # Load data
        data_1gpu = load_json_data(file_1gpu)
        data_ngpu = load_json_data(file_ngpu)

        all_data[ham_id] = (data_1gpu, data_ngpu)

        # Print summary
        for method in ["SpinOperator", "simple"]:
            q1, t1 = extract_time_data(data_1gpu, method)
            qn, tn = extract_time_data(data_ngpu, method)
            print(f"  {method}:")
            print(f"    1 GPU:  qubits={q1}, times={[f'{t:.3f}' for t in t1]}")
            print(f"    {args.num_gpus} GPUs: qubits={qn}, times={[f'{t:.3f}' for t in tn]}")

        # Create individual plot
        create_hamiltonian_plot(ham_id, ham_name, data_1gpu, data_ngpu,
                               args.num_gpus, output_dir)
        print()

    # Create combined plot
    print("Creating combined plot...")
    create_combined_plot(all_data, args.num_gpus, output_dir, hamiltonians)

    # ---- GPU Scaling Plots ----
    print("\n" + "="*60)
    print("Creating GPU scaling plots...")
    print("="*60 + "\n")

    # Load data from all GPU directories
    all_gpu_data = {}  # ham_id -> {num_gpus: data}

    for ham_id, ham_name in hamiltonians:
        print(f"Loading GPU scaling data for {ham_name}...")
        gpu_data = {}

        filename = f"HamLib-obs-{ham_id}.json"

        for num_gpus in gpu_counts:
            gpu_dir = data_dir / f"nvidia_g{num_gpus}"
            filepath = gpu_dir / filename
            data = load_json_data(filepath)
            gpu_data[num_gpus] = data

            # Print summary for simple method
            qubits, times = extract_time_data(data, "simple")
            if times:
                print(f"  {num_gpus} GPU(s): qubits={qubits}, times={[f'{t:.3f}' for t in times]}")

        all_gpu_data[ham_id] = gpu_data

        # Create individual GPU scaling plot
        create_gpu_scaling_plot(ham_id, ham_name, gpu_data, output_dir, gpu_counts)
        print()

    # Create combined GPU scaling plot
    print("Creating combined GPU scaling plot...")
    create_gpu_scaling_combined_plot(all_gpu_data, output_dir, hamiltonians, gpu_counts)

    print("\nDone!")


if __name__ == "__main__":
    main()
