#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "log_analysis.pdf"

def draw(plt):
    names = ['log-analysis/small', 'log-analysis/medium', 'log-analysis/full']
    results = get_results(names)

    sh_values = [results[n][0] for n in names]
    hs_values = [results[n][1] for n in names]

    draw_size_figure(plt, ['small', 'large', 'all'], sh_values, hs_values)

if __name__ == '__main__':
    draw(plt)
    plt.tight_layout()
    plt.savefig(fig_outfile)

# draw_size_table(names, results, 'bio4_tab.tex')
