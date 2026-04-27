#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib>=3.8.0",
#   "numpy>=1.24.0",
# ]
# ///
"""Generate speedup comparison plot from processed benchmark results.

Usage:
    ./plot_speedup.py                                        # Default: only Baseline and Sys
    ./plot_speedup.py --include-manual-opt                   # Include Manual-opt bars
    ./plot_speedup.py --include-bad-spec                     # Include Bad-spec bars
    ./plot_speedup.py -i data.json -o output.pdf             # Custom input/output paths
    ./plot_speedup.py --include-manual-opt --include-bad-spec  # Include both
"""

import json
import argparse
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Default paths
DATA_FILE = Path("data/python_hs_results.json")
FIG_OUTFILE = Path("img/python_speedup_bar.pdf")

# Set global font properties - sans serif for compact style
plt.rcParams.update({
    "font.size": 10,
    "font.family": "sans-serif",
    "font.sans-serif": [
        "Arial",
        "DejaVu Sans",
        "Liberation Sans",
        "Helvetica",
        "sans-serif",
    ],
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 12,
})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate speedup comparison plot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DATA_FILE,
        help=f"Input processed.json file (default: {DATA_FILE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=FIG_OUTFILE,
        help=f"Output plot file (default: {FIG_OUTFILE})",
    )
    parser.add_argument(
        "--include-manual-opt",
        action="store_true",
        help="Include Manual-opt (multiprocessing) bars in the plot",
    )
    parser.add_argument(
        "--include-bad-spec",
        action="store_true",
        help="Include Bad-spec bars in the plot",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Read processed results
    try:
        with open(args.input) as f:
            results = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found: {args.input}", file=sys.stderr)
        print(
            "Run process_results.py first to generate processed.json", file=sys.stderr
        )
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.input}: {e}", file=sys.stderr)
        return 1

    # Extract benchmark data
    data = results.get("data", [])
    if not data:
        print("Error: No benchmark data found in processed.json", file=sys.stderr)
        return 1

    # Prepare data for plotting
    benchmarks = []
    baseline_speedups = []  # Should all be 1.0 (baseline vs baseline)
    sys_speedups = []
    manual_opt_speedups = []
    bad_spec_speedups = []

    for entry in data:
        benchmark = entry["benchmark"]
        sub_mean = entry.get("sub_mean")
        spec_mean = entry.get("spec_mean")
        multi_mean = entry.get("multi_mean")
        bad_mean = entry.get("bad_mean")

        if sub_mean is None or spec_mean is None:
            print(
                f"Warning: Skipping {benchmark} - missing required timing data",
                file=sys.stderr,
            )
            continue

        # benchmark name is already the readable/display name from processed.json
        benchmarks.append(benchmark)

        # Baseline is always 1.0 (sub_mean / sub_mean)
        baseline_speedups.append(1.0)

        # Sys speedup: sub_mean / spec_mean
        sys_speedups.append(sub_mean / spec_mean)

        # Manual-opt speedup: sub_mean / multi_mean (if available)
        if multi_mean is not None:
            manual_opt_speedups.append(sub_mean / multi_mean)
        else:
            manual_opt_speedups.append(None)

        # Bad-spec speedup: sub_mean / bad_mean (if available)
        if bad_mean is not None:
            bad_spec_speedups.append(sub_mean / bad_mean)
        else:
            bad_spec_speedups.append(None)

    if not benchmarks:
        print("Error: No valid benchmark data to plot", file=sys.stderr)
        return 1

    # Setup plot
    num_benchmarks = len(benchmarks)

    # Determine number of bars per benchmark
    num_bars = 2  # Always have Baseline and Sys
    if args.include_manual_opt:
        num_bars += 1
    if args.include_bad_spec:
        num_bars += 1

    bar_width = 0.2
    fig, ax = plt.subplots(figsize=(16, 3.5))

    indices = np.arange(num_benchmarks)

    # Calculate bar positions
    bar_positions = []
    offset = -(num_bars - 1) * bar_width / 2

    # Always plot Baseline
    bar_positions.append(indices + offset)
    offset += bar_width

    # Conditionally add Manual-opt
    if args.include_manual_opt:
        bar_positions.append(indices + offset)
        offset += bar_width

    # Always plot Sys
    bar_positions.append(indices + offset)
    offset += bar_width

    # Conditionally add Bad-spec
    if args.include_bad_spec:
        bar_positions.append(indices + offset)

    # Plot bars
    bars = []
    labels = []

    # Baseline (Python)
    bars.append(
        ax.bar(
            bar_positions[0],
            baseline_speedups,
            bar_width,
            label="Baseline (Python)",
            color="#90EE90",
            edgecolor="black",
            linewidth=0.4,
        )
    )
    labels.append("Baseline (Python)")
    bar_idx = 1

    # Manual-opt (if included)
    if args.include_manual_opt:
        # Filter out None values for plotting
        manual_opt_plot = [v if v is not None else 0 for v in manual_opt_speedups]
        bars.append(
            ax.bar(
                bar_positions[bar_idx],
                manual_opt_plot,
                bar_width,
                label="Manual-opt",
                color="#FFDAB9",
                edgecolor="black",
                linewidth=0.4,
            )
        )
        labels.append("Manual-opt")
        bar_idx += 1

    # Sys
    bars.append(
        ax.bar(
            bar_positions[bar_idx],
            sys_speedups,
            bar_width,
            label="Sys",
            color="#ADD8E6",
            edgecolor="black",
            linewidth=0.4,
        )
    )
    labels.append("Sys")
    bar_idx += 1

    # Bad-spec (if included)
    if args.include_bad_spec:
        # Filter out None values for plotting
        bad_spec_plot = [v if v is not None else 0 for v in bad_spec_speedups]
        bars.append(
            ax.bar(
                bar_positions[bar_idx],
                bad_spec_plot,
                bar_width,
                label="Bad-spec",
                color="#FFB6C1",
                edgecolor="black",
                linewidth=0.4,
            )
        )
        labels.append("Bad-spec")

    # Styling
    ax.set_ylabel("Speedup vs Python", fontsize=11)
    ax.set_xticks(indices)
    ax.set_xticklabels(benchmarks, rotation=0, ha="center")
    ax.legend(labels, loc="upper left", frameon=True)
    ax.grid(axis="y", alpha=0.3, linestyle="--", linewidth=0.5)

    # Add horizontal line at y=1
    ax.axhline(y=1, color="gray", linestyle="-", linewidth=0.8, alpha=0.5)

    # Tight layout
    plt.tight_layout()

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Save figure
    plt.savefig(args.output, bbox_inches="tight", dpi=300)
    print(f"Saved plot to {args.output}")

    # Print statistics
    print(f"\nProcessed {num_benchmarks} benchmarks:")
    for i, benchmark in enumerate(benchmarks):
        print(f"  {benchmark}:")
        print(f"    Sys speedup: {sys_speedups[i]:.2f}x")
        if args.include_manual_opt and manual_opt_speedups[i] is not None:
            print(f"    Manual-opt speedup: {manual_opt_speedups[i]:.2f}x")
        if args.include_bad_spec and bad_spec_speedups[i] is not None:
            print(f"    Bad-spec speedup: {bad_spec_speedups[i]:.2f}x")

    return 0


if __name__ == "__main__":
    sys.exit(main())
