#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def parse_time_file(path: Path) -> float:
    return float(path.read_text().strip())

def collect_times(output_dir: Path):
    strace_times = {}
    fstrace_times = {}

    for entry in sorted(output_dir.iterdir()):
        if not entry.is_dir():
            continue
        strace_file = entry / "strace_time"
        fstrace_file = entry / "fstrace_time"
        if strace_file.exists() and fstrace_file.exists():
            strace_times[entry.name] = parse_time_file(strace_file)
            fstrace_times[entry.name] = parse_time_file(fstrace_file)

    return strace_times, fstrace_times

def main():
    parser = argparse.ArgumentParser(description="Log-log scatter plot: strace vs fstrace times")
    parser.add_argument("output_dir", help="Directory containing benchmark output subdirectories")
    parser.add_argument("plot_file", help="Output plot file (e.g. plot.pdf or plot.png)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    strace_times, fstrace_times = collect_times(output_dir)

    common = sorted(strace_times.keys() & fstrace_times.keys())
    if not common:
        print("No benchmarks with both strace_time and fstrace_time found.")
        return

    x = np.array([strace_times[k] for k in common])
    y = np.array([fstrace_times[k] for k in common])

    fig, ax = plt.subplots(figsize=(7, 6))

    ax.scatter(x, y, zorder=3)

    for name, xi, yi in zip(common, x, y):
        ax.annotate(name, (xi, yi), textcoords="offset points", xytext=(5, 3), fontsize=7)

    # y = x diagonal
    lim_min = min(x.min(), y.min()) * 0.8
    lim_max = max(x.max(), y.max()) * 1.25
    diag = np.array([lim_min, lim_max])
    ax.plot(diag, diag, linestyle="--", color="gray", linewidth=1, label="y = x", zorder=2)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim_min, lim_max)
    ax.set_ylim(lim_min, lim_max)
    ax.set_xlabel("strace time (s)")
    ax.set_ylabel("fstrace time (s)")
    ax.set_title("strace vs fstrace execution time")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    plt.savefig(args.plot_file)
    print(f"Saved plot to {args.plot_file}")

if __name__ == "__main__":
    main()
