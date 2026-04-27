#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "dgsh_fig.pdf"

def draw(plt):
    names = [
        'dgsh/1',
        'dgsh/5',
        'dgsh/6',
        'dgsh/7',
        'dgsh/8',
        'dgsh/17',
    ]
    ten_names = [name + '-10x' for name in names]
    hun_names = [name + '-100x' for name in names]
    one_results = get_results(names)
    ten_results = get_results(ten_names)
    hun_results = get_results(hun_names)
    sh_values = [[one_results[n][0] for n in names],
                 [ten_results[n][0] for n in ten_names],
                 [hun_results[n][0] for n in hun_names]]
    hs_values = [[one_results[n][1] for n in names],
                 [ten_results[n][1] for n in ten_names],
                 [hun_results[n][1] for n in hun_names]]

    draw_size_scatter_figure(plt, ['orig', '10×', '100×'], sh_values, hs_values)

if __name__ == '__main__':
    draw(plt)
    plt.tight_layout()
    plt.savefig(fig_outfile)

