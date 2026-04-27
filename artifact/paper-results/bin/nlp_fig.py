#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "nlp_fig.pdf"

def draw(plt):
    names = [
        'nlp/1_1',
        'nlp/2_1',
        'nlp/2_2',
        'nlp/3_1',
        'nlp/3_2',
        'nlp/3_3',
        'nlp/4_3',
        'nlp/4_3b',
        'nlp/6_1',
        'nlp/6_1_1',
        'nlp/6_1_2',
        'nlp/6_2',
        'nlp/6_3',
        'nlp/6_4',
        'nlp/6_5',
        'nlp/6_7',
        'nlp/7_1',
        'nlp/7_2',
        'nlp/8_1',
        'nlp/8.2_1',
        'nlp/8.2_2',
        'nlp/8.3_2',
        'nlp/8.3_3',
    ]
    ten_names = [name.replace('nlp', 'nlp10x') for name in names]
    hun_names = [name.replace('nlp', 'nlp100x') for name in names]
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

