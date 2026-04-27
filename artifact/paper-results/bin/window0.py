import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Update font settings to match style
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 20})  # Global font size

# Helper: geometric mean
def geomean(values):
    a = np.array(values, dtype=float)
    return a.prod() ** (1.0 / len(a))

# --- 1. Read CSV and compute overhead for window 0 ---
csv_path = "./data/hs_window.csv"
df = pd.read_csv(csv_path)

# filter on sh > 10 
df = df[df["sh"] > 10]

# Print benchmark names to debug which benchmarks are present
print("Benchmarks in input data:", df["benchmark"].unique())

# Calculate overhead as a decimal (will convert to percentage later)
df["overhead_0"] = df["hs window 0"] / df["sh"] - 1  # Subtract 1 to get overhead percentage

# Create a label combining benchmark and sub-benchmark
df["label"] = df["benchmark"] + ": " + df["sub-benchmark"]

# --- 2. Group by benchmark family and calculate geometric mean ---
# Extract benchmark family (assuming the benchmark column has format like "family/specific")
df["benchmark_family"] = df["benchmark"].apply(lambda x: x.split("/")[0] if "/" in x else x)

# Print benchmark families to debug
print("Benchmark families:", df["benchmark_family"].unique())

# For overhead, we need to calculate mean of (slowdown - 1) values
# Then add 1 back to get the slowdown, then subtract 1 again to get the percentage
family_stats = df.groupby("benchmark_family").agg({
    "overhead_0": lambda x: geomean(x + 1) - 1,  # Convert to slowdown, take geomean, convert back to overhead
    "benchmark": "first"  # Keep one benchmark name for color mapping
}).reset_index()

# Print family stats to debug
print("Family stats:", family_stats)

# Sort by overhead (least overhead at the top)
family_stats_sorted = family_stats.sort_values(by="overhead_0", ascending=True).reset_index(drop=True)

# --- 3. Define colorblind-friendly color mapping per benchmark family ---
benchmark_families = sorted(family_stats["benchmark_family"].unique())
# Using the same colorblind-friendly palette as varying_window.py
colors = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9', '#D55E00', '#F0E442', '#000000']
color_map = {bm: colors[i % len(colors)] for i, bm in enumerate(benchmark_families)}

# --- 4. Prepare y positions and colors for bars ---
y_positions = np.arange(len(family_stats_sorted))
bar_colors = [color_map[bm] for bm in family_stats_sorted["benchmark_family"]]

# --- 5. Create horizontal bar chart with matching style ---
fig = plt.figure(figsize=(5, 2.4))  # Slightly reduced height to trim whitespace
ax = fig.add_subplot(111)
bars = ax.barh(y_positions, family_stats_sorted["overhead_0"], color=bar_colors, edgecolor="black", linewidth=1, alpha=1)

# Set y-axis tick labels (each benchmark family) with 45 degree rotation
ax.set_yticks(y_positions)
ax.set_yticklabels(family_stats_sorted["benchmark_family"], fontsize=10, ha='right')

# --- 6. Set x-axis to display percentage overhead ---
ax.set_xlim(0, 0.5)  # Set limit to 50% overhead
ax.set_xticks(np.arange(0, 0.6, 0.1))  # Set ticks every 0.1
ax.set_xticklabels(["0%", "10%", "20%", "30%", "40%", "50%"], fontsize=10)

# Draw vertical baseline line at 0% overhead
baseline_line = ax.axvline(x=0, color="black", linestyle=":", linewidth=2, label="Baseline")

# Add grid matching varying_window.py
ax.grid(axis='x', linestyle='--', linewidth=0.5, alpha=0.7)

# Set border around the plot
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(True)
    ax.spines[spine].set_linewidth(1.0)
    ax.spines[spine].set_color('black')

# --- 7. Labeling and aesthetics ---
# ax.set_xlabel("Overhead", fontsize=12)

plt.tight_layout()
plt.subplots_adjust(left=0.25)  # Adjust left margin to accommodate rotated labels
plt.savefig("img/window0.pdf", dpi=300, bbox_inches='tight')  # Use tight bbox to trim whitespace
