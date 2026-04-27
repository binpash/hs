#!/usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 20})  # Global font size

# fig_outfile = FIG_OUTDIR / "io_heavy.pdf"
fig_outfile = FIG_OUTDIR / "open_heavy.pdf"


def retrieve_io_heavy_data():

    labels = ['sh', 'strace', 'parse', 'try', 'hs']
    # labels = ['sh', 'try', 'hs', 'hs-tmpfs', 'copy-only']

    sizes = ['4G', '8G', '16G']
    datas = []
    errors = []
    for label in labels:
        data = []
        error = []
        for size in sizes:
            d, e = mean_and_error(read_lines(DATA_DIR / 'io_heavy' / f'{label}_{size}'))
            data.append(d)
            error.append(e)
        datas.append(data)
        errors.append(error)

    return sizes, np.array(datas), errors



def retrieve_open_heavy_data():

    labels = ['sh', 'strace', 'parse', 'try', 'hs']

    sizes = [8192, 16384, 32768]
    datas = []
    errors = []
    for label in labels:
        data = []
        error = []
        for size in sizes:
            d, e = mean_and_error(read_lines(DATA_DIR / 'open_heavy' / f'{label}_{size}'))
            data.append(d)
            error.append(e)
        datas.append(data)
        errors.append(error)
    return sizes, np.array(datas), errors





# Create side-by-side plots
# Create a GridSpec layout
fig = plt.figure(figsize=(10, 4.5))
gs = GridSpec(1, 2, width_ratios=[2, 2])  # Two columns with different widths

sizes, datas, errors = retrieve_io_heavy_data()
labels = ['sh', '+strace', '+parse', '+sandbox', 'Sys']
sizes = ['4GB', '8GB', '16GB']

x = np.arange(len(sizes))
bar_width = 0.2
# bar_width = 0.18


# First subplot (larger)
ax1 = fig.add_subplot(gs[0])

print(f'strace: {datas[1]/datas[0]}')
print(f'parse: {datas[2]/datas[0]}')
print(f'try: {datas[3]/datas[0]}')
print(f'hs: {datas[4]/datas[0]}')

colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))  # Professional color palette
for i in range(len(labels)):
#     plt.bar(x + bar_width*(i-1.5), data[i], width=bar_width, label=labels[i], align='center')
    # axes[0].bar(i, data[i], width=bar_width, label=labels[i], align='center')
    ax1.bar(
        x + bar_width * (i - 1.5),
        datas[i],
        width=bar_width,
        label=labels[i],
        align='center',
        color=colors[i],
        edgecolor='black',
    )

ax1.set_xlabel('Size of Output', labelpad=10)
ax1.set_ylabel('Running Time (s)', labelpad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(sizes,)
# ax1.legend()
ax1.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)




## Open-heavy
sizes, datas, errors = retrieve_open_heavy_data()

print(f'strace: {datas[1]/datas[0]}')
print(f'parse: {datas[2]/datas[0]}')
print(f'try: {datas[3]/datas[0]}')
print(f'hs: {datas[4]/datas[0]}')

## Change the names for better plot
labels = ['sh', '+strace', '+parse', '+sandbox', 'Sys']

x = np.arange(len(sizes))

# Second subplot
ax2 = fig.add_subplot(gs[1])
colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))  # Professional color palette
for i in range(len(labels)):
    ax2.bar(
        x + bar_width * (i - 2),
        datas[i],
        width=bar_width,
        label=labels[i],
        align='center',
        color=colors[i],
        edgecolor='black',
    )

ax2.set_ylim(0, 10)
ax2.set_xlabel('# of Files Created', labelpad=10)
ax2.set_xticks(x)
ax2.set_xticklabels(sizes)
ax2.legend(fontsize=16)
ax2.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)


plt.tight_layout()
plt.savefig(fig_outfile, dpi=300)
