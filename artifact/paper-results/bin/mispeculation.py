import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from config import *
from itertools import repeat, chain
from dataclasses import dataclass
from cpu_time import read_log, read_logs, Execution
from matplotlib.patches import Rectangle, Patch
from matplotlib.transforms import ScaledTranslation

# PDF styling
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['hatch.linewidth'] = 5.0
plt.rcParams['hatch.color'] = 'white'

# -----------------------------
# Output PDF (combined figure)
# -----------------------------
fig_outfile = FIG_OUTDIR / "execution_and_misspeculation.pdf"

# -----------------------------
# LEFT PLOT: Execution Bars
# -----------------------------
data_path = DATA_DIR / "misspeculation_log"
fulltrace = read_log(data_path / "max_temp" / "medium" / "stderr_hs")

data = fulltrace.execs
commit = list(fulltrace.commits.values())
x = list(fulltrace.commits.keys())

# Create side-by-side figure
fig, (ax2, ax1) = plt.subplots(1, 2, figsize=(6, 3), width_ratios=[1, 1.8])

# Normalize start times
start_time = data[0].start
finals = {}
for e in data:
    e.start -= start_time
    e.end -= start_time
    if e.cmd not in finals or e.end > finals[e.cmd].end:
        finals[e.cmd] = e

commit = [c - start_time for c in commit]

# Background strips
for i in range(10):
    rect = Rectangle(
        (0, 5 * i + 0.7),
        560,
        4.6,
        linewidth=0,
        facecolor='lightblue',
        alpha=0.3,
        zorder=-1
    )
    ax1.add_patch(rect)

proxy = Patch(facecolor='lightblue', edgecolor='blue', alpha=0.5, label='Iteration')
ax1.legend(handles=[proxy])

# Categorize executions
data_wrong = [e for e in data if e not in finals.values() and e.cmd in x]
data_right = [e for e in data if e not in data_wrong and e.spec and e.cmd in x]
data_canon = [e for e in data if e not in data_wrong and not e.spec and e.cmd in x]

# Wrong speculation bars (red)
bars = ax1.barh(
    [x.index(e.cmd) for e in data_wrong],
    [e.end - e.start for e in data_wrong],
    left=[e.start for e in data_wrong],
    height=0.5,
    color='red',
    edgecolor='black',
    linewidth=0.5,
    label='wrong speculation'
)
for b in bars:
    b._hatch_color = matplotlib.colors.to_rgba('white')

# Correct speculation bars (light green)
bars = ax1.barh(
    [x.index(e.cmd) for e in data_right],
    [e.end - e.start for e in data_right],
    left=[e.start for e in data_right],
    height=0.5,
    color='lightgreen',
    edgecolor='black',
    linewidth=0.5,
    label='correct speculation'
)
for b in bars:
    b._hatch_color = matplotlib.colors.to_rgba('white')

# Canonical execution bars (green)
ax1.barh(
    [x.index(e.cmd) for e in data_canon],
    [e.end - e.start for e in data_canon],
    left=[e.start for e in data_canon],
    height=0.5,
    color='green',
    edgecolor='black',
    linewidth=0.5,
    label='direct execution'
)

# Commit dots
ax1.scatter(commit, list(range(len(x))), marker='o', color='blue', s=7, label='commit')

ax1.grid(axis='x', linestyle='--', linewidth=1, alpha=0.7)
ax1.set_yticks([])
ax1.set_yticklabels([])
ax1.set_ylim(-0.5, 40.5)
ax1.set_xlim(0, 400)
## Zoom in more
ax1.set_ylim(6.5, 40.5)
ax1.set_xlim(100, 450)
ax1.set_xlabel("Time (s)")
ax1.invert_yaxis()
ax1.legend(loc='upper right')


# -----------------------------
# RIGHT PLOT: Misspeculation Barplot (merged sklearn + sklearn_large)
# -----------------------------

# Pretty labels
pretty_bench_labels = {
    'teraseq': 'TERA-Seq',
    'bio4': 'Genomics',
    'sklearn': 'SkLearn',          # merged label
    'sklearn_large': 'SkLearnLarge',
    'dgsh': 'DGSH',
    'nlp': 'NLP',
    'max_temp': 'NOAA',
    'unix_50': 'Unix50',
    'bus-analytics': 'COVID-mts',
    'log-analysis': 'LogAnalysis',
    'web-index': 'WebIndex',
}

# Load logs
names, count_overhead, time_overhead = read_logs()

# Convert to numpy arrays so deletion is easy
names = np.array(names)
count_overhead = np.array(count_overhead)
time_overhead = np.array(time_overhead)

# -----------------------------
# MERGE sklearn + sklearn_large
# -----------------------------
merge_keys = ["sklearn", "sklearn_large"]

# Find indices of these benchmarks (if present)
merge_indices = [np.where(names == k)[0][0] for k in merge_keys if k in names]

if len(merge_indices) == 2:
    i1, i2 = merge_indices

    # Average the values
    merged_count = (count_overhead[i1] + count_overhead[i2]) / 2
    merged_time = (time_overhead[i1] + time_overhead[i2]) / 2

    ## Just keep sklearn_large
    merged_count = count_overhead[i2]
    merged_time = time_overhead[i2]

    # Create new arrays with merged row replacing sklearn, removing sklearn_large
    keep_mask = np.ones(len(names), dtype=bool)
    keep_mask[i2] = False  # remove sklearn_large

    names = names[keep_mask]
    count_overhead = count_overhead[keep_mask]
    time_overhead = time_overhead[keep_mask]

    # Replace sklearn entry with merged result
    new_idx = np.where(names == "sklearn")[0][0]
    count_overhead[new_idx] = merged_count
    time_overhead[new_idx] = merged_time

# -----------------------------
# Compute misspec rate
# -----------------------------
misspec = 100 * time_overhead / (time_overhead + 1)
idx = np.arange(len(names))

# Convert labels
pretty_names = [pretty_bench_labels.get(n, n) for n in names]

# -----------------------------
# Plot
# -----------------------------
ax2.barh(
    idx,
    misspec,
    color='#1f77b4',
    edgecolor='black',
    linewidth=1
)

ax2.set_xlabel("Mis-speculation rate (%)")
ax2.set_xticks([0, 10, 20, 30, 40, 50])
ax2.set_xlim(0, 50)

ax2.set_yticks(idx)
ax2.set_yticklabels(pretty_names)
ax2.invert_yaxis()
ax2.grid(axis='x', linestyle='--', linewidth=1, alpha=0.7)


## TODO: Move the labels inside the figure to save space

# Example: make deeper padding the lower the label is
# paddings = [
#     20,
#     20,
#     20,
#     20,
#     20,
#     20,
#     20,
#     20
# ]  # customize as needed

# for lbl, pad in zip(labels, paddings):
#     lbl.set_transform(lbl.get_transform() +
#                       ScaledTranslation(pad / 72, 0, fig.dpi_scale_trans))


# ax2.tick_params(axis='y', pad=-10)
# for label in ax2.get_yticklabels():
#     label.set_horizontalalignment('right')



# -----------------------------
# Final Layout + Save
# -----------------------------
plt.tight_layout()
plt.savefig(fig_outfile, bbox_inches='tight')
print("Saved combined figure to:", fig_outfile)
