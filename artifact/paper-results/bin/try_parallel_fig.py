#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 20})  # Global font size

fig_outfile = FIG_OUTDIR / "try-parallel.pdf"

x = np.array([1, 2, 4, 8, 16, 32, 64])
y = np.array([mean_and_error(read_lines(DATA_DIR / 'try_parallel' / f'try_{i}'))[0] for i in x])
y_hs = np.array([mean_and_error(read_lines(DATA_DIR / 'try_parallel' / f'hs_{i}'))[0] for i in x])
y = 1024/y
y_hs = 1024/y_hs
y_ideal = x*y[0]

# Creating the line plot
plt.figure(figsize=(10, 5))
plt.xlim(0, 65)
plt.ylim(0, 60)
plt.plot(x, y_hs, marker='o', linestyle='-', linewidth=2, markersize=6, 
         label='Sys')
plt.plot(x, y, marker='o', linestyle='-', linewidth=2, markersize=6, 
         label='sandbox-only')
plt.plot(x, y_ideal, marker='o', linestyle='--', linewidth=2, markersize=6,
         label='ideal scaling')
plt.xlabel("Parallelization")
plt.ylabel("echo/s")
plt.ylim(0, 100)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.legend()
plt.tight_layout()
plt.savefig(fig_outfile)
