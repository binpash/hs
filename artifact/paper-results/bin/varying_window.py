import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Helper: geometric mean --- (kept for reference but won't be used)
def geomean(values):
    a = np.array(values, dtype=float)
    return a.prod() ** (1.0 / len(a))

# Update font settings to match style
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 20})  # Global font size

# 1) Read CSV
df = pd.read_csv("data/hs_window.csv")

# Filter out rows where sh is less than 10
df = df[df["sh"] >= 10]

# ignore 0 window column
df = df.drop(columns=["hs window 0"])

# 2) Melt from wide to long format
long_df = df.melt(
    id_vars=["benchmark", "sub-benchmark", "sh"],
    var_name="window",
    value_name="hs_time"
)

# 3) Clean up window labels
long_df["window_size"] = (
    long_df["window"]
    .str.replace("hs window ", "", regex=False)
    .replace("infinite", "∞")
)

# 4) Order window sizes
window_order = ["0", "1", "5", "10", "15", "20", "30", "∞"]
long_df["window_size"] = pd.Categorical(
    long_df["window_size"], categories=window_order, ordered=True
)

# 5) Calculate speedup
long_df["speedup"] = long_df["sh"] / long_df["hs_time"]

# Use raw data directly instead of geomean
windows_sorted = [w for w in window_order if w in long_df["window_size"].unique()]
data_by_window = []
for w in windows_sorted:
    speeds = long_df.loc[long_df["window_size"] == w, "speedup"].values
    data_by_window.append(speeds)
    print(w)
    print(np.median(speeds))
    print(speeds)

# 9) Color & marker style, using more vibrant colors
benchmark_list = sorted(long_df["benchmark"].unique())
# Updated colorblind-friendly palette
# Using a colorblind-friendly palette with high contrast
# Source: https://davidmathlogic.com/colorblind/
colors = ['#0072B2', '#E69F00', '#009E73', '#CC79A7', '#56B4E9', '#D55E00', '#F0E442', '#000000']
color_map = {bm: c for bm, c in zip(benchmark_list, colors)}
marker_map = {
    bm: m for bm, m in zip(benchmark_list, ["o","s","^","v","d","X","<",">"])
}

# 10) Create figure with size more similar to varying_size.py
fig = plt.figure(figsize=(10, 4.5))
ax = fig.add_subplot(111)

# 11) Boxplot with patch_artist for colored boxes - using raw data
bp = ax.boxplot(
    data_by_window,
    positions=range(1, len(windows_sorted)+1),
    patch_artist=True,
    showfliers=False,
    widths=0.5
)

# Style the boxes with edgecolor and specific styling
for box in bp["boxes"]:
    box.set_facecolor('lightblue')
    box.set_edgecolor('black')
    box.set_linewidth(1)
for median in bp["medians"]:
    median.set_color('red')
    median.set_linewidth(2)
for whisker in bp["whiskers"]:
    whisker.set_color('black')
for cap in bp["caps"]:
    cap.set_color('black')

# Force x‐axis tick labels
ax.set_xticks(range(1, len(windows_sorted)+1))
ax.set_xticklabels(windows_sorted)

# 12) Overlay raw data points (each benchmark entry)
plotted = set()
for i, w in enumerate(windows_sorted, start=1):
    subdf = long_df[long_df["window_size"] == w]
    for _, row in subdf.iterrows():
        bm = row["benchmark"]
        x_jitter = np.random.normal(loc=i, scale=0.06)  # slight jitter
        ax.plot(
            x_jitter, row["speedup"],
            marker=marker_map[bm],
            markersize=5,
            color=color_map[bm],
            linestyle="None",
            label=bm if bm not in plotted else None,
            alpha=0.85
        )
        plotted.add(bm)

# 13) Y‐axis in log2 scale with custom ticks
ax.set_yscale("log", base=2)
ax.set_ylim(1/8, 32)
ax.set_yticks([1/8, 1/4, 1/2, 1, 2, 4, 8, 16, 32])
ax.set_yticklabels(["8", "4", "2", "1", "2", "4", "8", "16", "32"])

# Draw baseline line using dotted style
ax.axhline(y=1, color='black', linestyle=':', linewidth=2, label='Baseline')

# 14) Add grid
ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)

# Set border
for spine in ['top', 'right', 'left', 'bottom']:
    ax.spines[spine].set_visible(True)
    ax.spines[spine].set_linewidth(1.0)
    ax.spines[spine].set_color('black')

ax.legend(
    loc="upper left", 
    frameon=True, 
    ncol=5,
    fontsize=12,
    labelspacing=0.001,  # Reduced label spacing for smaller vertical gap between columns
    borderaxespad=0.1,   # Smaller margin around the legend
    handletextpad=0.5,   # Reduced space between marker and text
    columnspacing=0.8    # Reduced horizontal gap between columns
)

# 16) Labels with matching style
ax.set_xlabel("Window Size", fontsize=20)
ax.set_ylabel("Slowdown     Speedup     ", fontsize=20, ha='center')

plt.tight_layout()
plt.savefig("img/varying_window_sizes.pdf", dpi=300)
