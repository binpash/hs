#!/usr/bin/env python3

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from pathlib import Path

# Update font settings to match style
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 20})  # Global font size

# Define output paths
FIG_OUTDIR = Path('img')
combined_outfile = FIG_OUTDIR / "try_parallel_and_window0.pdf"

# Create the figure with two subplots side by side
fig = plt.figure(figsize=(10, 4.5))
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])

# ================ LEFT PLOT: try_parallel_fig.py ================
ax1 = fig.add_subplot(gs[0])

# Load data for try_parallel plot
DATA_DIR = Path('data')
try_parallel_dir = DATA_DIR / 'try_parallel'

def mean_and_error(nums):
    mean = sum(nums)/len(nums)
    if len(nums) > 1:
        error = np.sqrt(sum([(n-mean)*(n-mean) for n in nums])/(len(nums)-1))
    else:
        error = None
    return mean, error

def read_lines(fname):
    with open(fname) as f:
        lines = f.read().strip().split('\n')
        nums = [float(l) for l in lines]
    return nums

# Recreate the try_parallel plot
x = np.array([1, 2, 4, 8, 16, 32, 64])
y = np.array([mean_and_error(read_lines(try_parallel_dir / f'try_{i}'))[0] for i in x])
y_hs = np.array([mean_and_error(read_lines(try_parallel_dir / f'hs_{i}'))[0] for i in x])
y = 1024/y
y_hs = 1024/y_hs
y_ideal = x*y[0]

ax1.set_xlim(0, 65)
ax1.set_ylim(0, 100)
ax1.plot(x, y_hs, marker='o', linestyle='-', linewidth=2, markersize=6, 
        label='Sys')
ax1.plot(x, y, marker='o', linestyle='-', linewidth=2, markersize=6, 
        label='sandbox-only')
ax1.plot(x, y_ideal, marker='o', linestyle='--', linewidth=2, markersize=6,
        label='ideal scaling')
ax1.set_xlabel("Parallelization")
ax1.set_ylabel("echo/s")
ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
ax1.legend()

# Set borders around the plot
for spine in ['top', 'right', 'left', 'bottom']:
    ax1.spines[spine].set_visible(True)
    ax1.spines[spine].set_linewidth(1.0)
    ax1.spines[spine].set_color('black')

# ================ RIGHT PLOT: window0.py ================
ax2 = fig.add_subplot(gs[1])

# Helper function for geometric mean
def geomean(values):
    a = np.array(values, dtype=float)
    return a.prod() ** (1.0 / len(a))

# Load data for window0 plot
csv_path = DATA_DIR / "hs_window.csv"
df = pd.read_csv(csv_path)

# Exec time >= 10s
df = df[df["sh"] >= 10]

# Calculate overhead as a decimal (will convert to percentage later)
df["overhead_0"] = df["hs window 0"] / df["sh"] - 1  # Subtract 1 to get overhead percentage

# Create a label combining benchmark and sub-benchmark
df["label"] = df["benchmark"] + ": " + df["sub-benchmark"]

# Extract benchmark family
df["benchmark_family"] = df["benchmark"].apply(lambda x: x.split("/")[0] if "/" in x else x)

# For overhead, we need to calculate mean of (slowdown - 1) values
# Then add 1 back to get the slowdown, then subtract 1 again to get the percentage
family_stats = df.groupby("benchmark_family").agg({
    "overhead_0": lambda x: geomean(x + 1) - 1,  # Convert to slowdown, take geomean, convert back to overhead
    "benchmark": "first"  # Keep one benchmark name for color mapping
}).reset_index()

# Sort by overhead (least overhead at the top)
family_stats_sorted = family_stats.sort_values(by="overhead_0", ascending=True).reset_index(drop=True)

# Define colorblind-friendly color mapping per benchmark family
benchmark_families = sorted(family_stats["benchmark_family"].unique())
colors = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9', '#D55E00', '#F0E442', '#000000']
color_map = {bm: colors[i % len(colors)] for i, bm in enumerate(benchmark_families)}

# Prepare y positions and colors for bars
y_positions = np.arange(len(family_stats_sorted))
bar_colors = [color_map[bm] for bm in family_stats_sorted["benchmark_family"]]

# Create horizontal bar chart
bars = ax2.barh(y_positions, family_stats_sorted["overhead_0"], color=bar_colors, edgecolor="black", linewidth=1, alpha=1)

# Set y-axis tick labels (each benchmark family) with 45 degree rotation
ax2.set_yticks(y_positions)
ax2.set_yticklabels(family_stats_sorted["benchmark_family"], fontsize=14, rotation=45, ha='right')

# Set x-axis to display percentage overhead
ax2.set_xlim(0, 0.5)  # Set limit to 50% overhead
ax2.set_xticks(np.arange(0, 0.6, 0.1))  # Set ticks every 0.1
ax2.set_xticklabels(["0%", "10%", "20%", "30%", "40%", "50%"], fontsize=16)

# Draw vertical baseline line at 0% overhead
baseline_line = ax2.axvline(x=0, color="black", linestyle=":", linewidth=2, label="Baseline")

# Add grid matching varying_window.py
ax2.grid(axis='x', linestyle='--', linewidth=0.5, alpha=0.7)

# Set border around the plot
for spine in ['top', 'right', 'left', 'bottom']:
    ax2.spines[spine].set_visible(True)
    ax2.spines[spine].set_linewidth(1.0)
    ax2.spines[spine].set_color('black')

# Labeling and aesthetics
ax2.set_xlabel("Overhead", fontsize=20)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(wspace=0.3)  # Adjust space between plots

# Save the combined figure
plt.savefig(combined_outfile, dpi=300, bbox_inches='tight')
print(f"Combined plot saved to {combined_outfile}") 