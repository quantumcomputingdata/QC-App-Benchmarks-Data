"""
Plot Benchmark Scaling Results for QED-C Fidelity Benchmarks

Reads JSON data files (DATA-nvidia-Ng-1.json) and creates plots showing
execution time scaling across different GPU counts for each benchmark.

Each plot shows:
- X-axis: Number of qubits
- Y-axis: Average execution time (log scale)
- One trace per GPU count (1, 2, 4, 8, 16, 32, 64, 128, 256)

Usage:
    python plot_benchmark_scaling.py [--data_dir PATH] [--output_dir PATH] [--data_suffix NAME]

Examples:
    # Use data from __data/ and output to __images/
    python plot_benchmark_scaling.py

    # Use archived data from __data/Perlmutter-80GB-260310/ and output to __images/Perlmutter-80GB-260310/
    python plot_benchmark_scaling.py --data_suffix Perlmutter-80GB-260310
    python plot_benchmark_scaling.py -suffix Perlmutter-80GB-260310
"""

import json
import os
import re
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


# Display name mappings for benchmarks (optional, for nicer labels)
BENCHMARK_NAMES = {
    "Benchmark Results - Hidden Shift - cudaq": "Hidden Shift",
    "Benchmark Results - Phase Estimation - cudaq": "Phase Estimation",
    "Benchmark Results - Quantum Fourier Transform (1) - cudaq": "Quantum Fourier Transform",
    "Benchmark Results - Bernstein-Vazirani - cudaq": "Bernstein-Vazirani",
    "Benchmark Results - Grover's Search - cudaq": "Grover's Search",
}

# Preferred ordering for benchmarks
BENCHMARK_ORDER = [
    "Benchmark Results - Quantum Fourier Transform (1) - cudaq",
    "Benchmark Results - Phase Estimation - cudaq",
    "Benchmark Results - Hidden Shift - cudaq",
    "Benchmark Results - Bernstein-Vazirani - cudaq",
    "Benchmark Results - Grover's Search - cudaq",
]


def discover_gpu_files(data_dir):
    """
    Scan data directory for DATA-nvidia-Ng-1.json files and return
    sorted list of (gpu_count, filepath) tuples.
    """
    import glob

    gpu_files = []

    for filepath in glob.glob(str(data_dir / "DATA-nvidia-*g-1.json")):
        filename = os.path.basename(filepath)
        # Extract GPU count from "DATA-nvidia-{N}g-1.json"
        match = re.match(r'DATA-nvidia-(\d+)g-1\.json$', filename)
        if match:
            gpu_count = int(match.group(1))
            gpu_files.append((gpu_count, filepath))

    # Sort by GPU count
    return sorted(gpu_files, key=lambda x: x[0])


def discover_benchmarks(gpu_files):
    """
    Scan all GPU files to discover available benchmarks.
    Returns sorted list of (benchmark_key, display_name) tuples.
    """
    benchmarks = set()

    for gpu_count, filepath in gpu_files:
        with open(filepath, 'r') as f:
            data = json.load(f)
            benchmarks.update(data.keys())

    # Sort by preferred order, then alphabetically for unknown benchmarks
    def sort_key(bm_key):
        if bm_key in BENCHMARK_ORDER:
            return (0, BENCHMARK_ORDER.index(bm_key))
        return (1, bm_key)

    result = []
    for bm_key in sorted(benchmarks, key=sort_key):
        display_name = BENCHMARK_NAMES.get(bm_key, bm_key)
        result.append((bm_key, display_name))

    return result


def load_all_data(gpu_files):
    """
    Load data from all GPU files.
    Returns dict: gpu_count -> {benchmark_key -> group_metrics}
    """
    all_data = {}

    for gpu_count, filepath in gpu_files:
        with open(filepath, 'r') as f:
            data = json.load(f)
            all_data[gpu_count] = data

    return all_data


def get_gpu_style(gpu_count, gpu_counts):
    """
    Generate marker, color, and label for a given GPU count.
    Uses a consistent color progression based on position in the list.
    """
    markers = ['o-', 's-', '^-', 'd-', 'v-', '<-', '>-', 'p-', 'h-', '*-']
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(gpu_counts)))

    idx = gpu_counts.index(gpu_count) if gpu_count in gpu_counts else 0
    marker = markers[idx % len(markers)]
    color = colors[idx]
    label = f"{gpu_count} GPU" if gpu_count == 1 else f"{gpu_count} GPUs"

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


def make_safe_filename(name):
    """Convert benchmark name to safe filename."""
    # Remove common prefixes/suffixes
    name = name.replace("Benchmark Results - ", "")
    name = name.replace(" - cudaq", "")
    # Replace spaces and special chars with underscores
    name = re.sub(r'[^a-zA-Z0-9]+', '_', name)
    # Remove trailing underscores and convert to lowercase
    name = name.strip('_').lower()
    return name


def create_benchmark_plot(bm_key, bm_name, all_data, gpu_counts, output_dir):
    """
    Create a plot showing GPU scaling for one benchmark.
    Shows execution time vs qubits with one trace per GPU count.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    has_data = False
    all_qubits = set()

    for gpu_count in gpu_counts:
        gpu_data = all_data.get(gpu_count, {})
        bm_data = gpu_data.get(bm_key, {})
        group_metrics = bm_data.get('group_metrics', {})

        groups = group_metrics.get('groups', [])
        exec_times = group_metrics.get('avg_exec_times', [])

        if groups and exec_times:
            # Convert group strings to integers
            qubits = [int(g) for g in groups]
            times = exec_times

            has_data = True
            all_qubits.update(qubits)

            marker, color, label = get_gpu_style(gpu_count, gpu_counts)
            ax.plot(qubits, times, marker, label=label, color=color,
                   linewidth=2, markersize=8)

    if not has_data:
        print(f"  No data found for {bm_name}, skipping plot")
        plt.close(fig)
        return None

    # Configure plot
    ax.set_xlabel("Number of Qubits", fontsize=12)
    ax.set_ylabel("Execution Time (seconds)", fontsize=12)
    ax.set_title(f"GPU Scaling: {bm_name}", fontsize=14)
    ax.set_yscale('log')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Set x-ticks to actual qubit values
    if all_qubits:
        sorted_qubits = sorted(all_qubits)
        ax.set_xticks(sorted_qubits)

    plt.tight_layout()

    # Save plot
    safe_name = make_safe_filename(bm_key)
    output_file = save_plot(fig, output_dir, f"benchmark_scaling_{safe_name}")

    plt.close(fig)
    return output_file


def create_combined_plot(benchmarks, all_data, gpu_counts, output_dir):
    """
    Create a combined figure with subplots for all benchmarks.
    """
    num_bms = len(benchmarks)
    if num_bms == 0:
        print("  No benchmarks to plot")
        return None

    fig, axes = plt.subplots(1, num_bms, figsize=(5.5 * num_bms, 5))
    if num_bms == 1:
        axes = [axes]

    for idx, (bm_key, bm_name) in enumerate(benchmarks):
        ax = axes[idx]
        all_qubits = set()

        for gpu_count in gpu_counts:
            gpu_data = all_data.get(gpu_count, {})
            bm_data = gpu_data.get(bm_key, {})
            group_metrics = bm_data.get('group_metrics', {})

            groups = group_metrics.get('groups', [])
            exec_times = group_metrics.get('avg_exec_times', [])

            if groups and exec_times:
                qubits = [int(g) for g in groups]
                times = exec_times

                all_qubits.update(qubits)

                marker, color, label = get_gpu_style(gpu_count, gpu_counts)
                ax.plot(qubits, times, marker, label=label, color=color,
                       linewidth=2, markersize=6)

        ax.set_xlabel("Qubits", fontsize=11)
        ax.set_ylabel("Time (sec)", fontsize=11)
        ax.set_title(bm_name, fontsize=12)
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)

        if all_qubits:
            sorted_qubits = sorted(all_qubits)
            ax.set_xticks(sorted_qubits)

        # Only show legend on first plot
        if idx == 0:
            ax.legend(loc='upper left', fontsize=8)

    plt.suptitle("QED-C Benchmark GPU Scaling", fontsize=14, y=1.02)
    plt.tight_layout()

    output_file = save_plot(fig, output_dir, "benchmark_scaling_combined")

    plt.close(fig)
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Plot benchmark scaling results")
    parser.add_argument("--data_dir", type=str, default="__data",
                       help="Directory containing DATA-nvidia-*g-1.json files")
    parser.add_argument("--output_dir", type=str, default="__images",
                       help="Directory to save plot images")
    parser.add_argument("--data_suffix", "-suffix", type=str, default=None,
                       help="Subdirectory name for archived data (e.g., 'Perlmutter-80GB-260310')")

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent

    # If suffix provided, look in subdirectory for data and create subdirectory for output
    if args.data_suffix:
        data_dir = script_dir / args.data_dir / args.data_suffix
        output_dir = script_dir / args.output_dir / args.data_suffix
        print(f"Using archived data: {args.data_suffix}")
    else:
        data_dir = script_dir / args.data_dir
        output_dir = script_dir / args.output_dir

    print(f"Data directory:   {data_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Discover GPU files
    gpu_files = discover_gpu_files(data_dir)
    if not gpu_files:
        print(f"No DATA-nvidia-*g-1.json files found in {data_dir}/")
        return

    gpu_counts = [gf[0] for gf in gpu_files]
    print(f"Discovered {len(gpu_files)} GPU configuration(s): {gpu_counts}")

    # Discover benchmarks
    benchmarks = discover_benchmarks(gpu_files)
    if not benchmarks:
        print("No benchmarks found in data files")
        return

    print(f"\nDiscovered {len(benchmarks)} benchmark(s):")
    for bm_key, bm_name in benchmarks:
        print(f"  - {bm_name}")
    print()

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load all data
    print("Loading data...")
    all_data = load_all_data(gpu_files)

    # Create individual benchmark plots
    print("\nCreating individual benchmark plots...")
    for bm_key, bm_name in benchmarks:
        print(f"Processing {bm_name}...")

        # Print data summary
        for gpu_count in gpu_counts:
            gpu_data = all_data.get(gpu_count, {})
            bm_data = gpu_data.get(bm_key, {})
            group_metrics = bm_data.get('group_metrics', {})
            groups = group_metrics.get('groups', [])
            exec_times = group_metrics.get('avg_exec_times', [])
            if groups:
                print(f"  {gpu_count} GPU(s): qubits={groups}, times={[f'{t:.3f}' for t in exec_times]}")

        create_benchmark_plot(bm_key, bm_name, all_data, gpu_counts, output_dir)
        print()

    # Create combined plot
    print("Creating combined plot...")
    create_combined_plot(benchmarks, all_data, gpu_counts, output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
