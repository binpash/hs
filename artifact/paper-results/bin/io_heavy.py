#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "io_heavy.pdf"

labels = ['sh', 'hs', 'hs-tmpfs', 'copy-only']

sizes = [8192, 16384, 32768]
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

x = np.arange(len(labels))
bar_width = 0.2

labels[1] = 'SYS'
labels[2] = 'SYS-tmpfs'

x = np.arange(len(configurations))
for i in range(len(labels)):
#     plt.bar(x + bar_width*(i-1.5), data[i], width=bar_width, label=labels[i], align='center')
    plt.bar(i, data[i], width=bar_width, label=labels[i], align='center')

plt.xlabel('Configuration')
plt.ylabel('Running Time (s)')
plt.xticks(x, labels)
plt.legend()

plt.tight_layout()
plt.savefig(fig_outfile)
