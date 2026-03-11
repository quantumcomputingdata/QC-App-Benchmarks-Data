"""
Plot Parallel Execution Results for HamLib Benchmarks

Reads JSON data files from nvidia_g1 and nvidia_g16 directories and creates
plots comparing single GPU vs 16-GPU MPI execution times for each Hamiltonian.

Each plot shows 4 traces:
- SpinOperator, 1 GPU (baseline)
- SpinOperator, 16 GPUs (mgpu mode)
- simple, 1 GPU (baseline)
- simple, 16 GPUs (-pm mpi parallel circuit execution)

Usage:
    python plot_parallel_execution.py [--data_dir PATH] [--output_dir PATH] [--num_gpus N]
"""

import json
import os
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


# Hamiltonian configurations: (filename_pattern, display_name)
HAMILTONIANS = [
    ("condensedmatter_tfim_tfim", "TFIM (Transverse Field Ising Model)"),
    ("condensedmatter_bosehubbard_BH_D-1_d-4", "Bose-Hubbard"),
    ("chemistry_electronic_standard_H2", "H2 (Hydrogen)"),
]


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
    output_file = os.path.join(output_dir, f"parallel_exec_{ham_id}.png")
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_file}")

    plt.close(fig)
    return output_file


def create_combined_plot(all_data, num_gpus, output_dir):
    """
    Create a combined figure with subplots for all Hamiltonians.
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    for idx, (ham_id, ham_name) in enumerate(HAMILTONIANS):
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

    output_file = os.path.join(output_dir, "parallel_exec_combined.png")
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_file}")

    plt.close(fig)
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Plot parallel execution results")
    parser.add_argument("--data_dir", type=str, default="__data",
                       help="Base directory containing nvidia_g* subdirectories")
    parser.add_argument("--output_dir", type=str, default=".",
                       help="Directory to save plot images")
    parser.add_argument("--num_gpus", type=int, default=16,
                       help="Number of GPUs for MPI comparison (default: 16)")

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    data_dir = script_dir / args.data_dir
    output_dir = script_dir / args.output_dir

    # Directory names
    dir_1gpu = data_dir / "nvidia_g1"
    dir_ngpu = data_dir / f"nvidia_g{args.num_gpus}"

    print(f"Loading data from:")
    print(f"  1 GPU:        {dir_1gpu}")
    print(f"  {args.num_gpus} GPUs:       {dir_ngpu}")
    print()

    # Load and plot each Hamiltonian
    all_data = {}

    for ham_id, ham_name in HAMILTONIANS:
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
    create_combined_plot(all_data, args.num_gpus, output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
