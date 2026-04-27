#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "noaa_fig.pdf"

def draw(plt):
    names = ['max_temp/tiny', 'max_temp/small', 'max_temp/medium', 'max_temp/large']
    results = get_results(names)

    sh_values = [results[n][0] for n in names]
    hs_values = [results[n][1] for n in names]

    draw_size_figure(plt, ['tiny', 'small', 'medium', 'large'], sh_values, hs_values)

if __name__ == '__main__':
    draw(plt)
    plt.tight_layout()
    plt.savefig(fig_outfile)

