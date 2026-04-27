#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
from config import *

plt.rcParams['pdf.fonttype'] = 42

fig_outfile = FIG_OUTDIR / "teraseq.pdf"

def draw(plt):
    names = ['teraseq/dRNASeq', 'teraseq/mouse_SIRV', 'teraseq/5TERA3',
             'teraseq/Akron5Seq', 'teraseq/RNASeq', 'teraseq/TERA3',
             'teraseq/5TERA', 'teraseq/5TERA-short', 'teraseq/RiboSeq']
    results = get_results(names)
    with open(DATA_DIR / "output_teraseq_orig.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            name, orig_time = row
            assert name in results
            results[name] = (*results[name], float(orig_time))

    sh_numbers = np.array([results[n][0] for n in names])
    hs_numbers = np.array([results[n][1] for n in names])
    orig_numbers = np.array([results[n][2] for n in names])

    fig = plt.figure(figsize=(6, 3))

    # Add a subplot (1 row, 1 column, 1st position)
    ax = fig.add_subplot(1, 1, 1)
    x = np.arange(len(names))
    barwidth=0.4
    ax.set_xlabel('Benchmark')
    ax.set_ylabel('Relative speed up')
    ax.bar(x-0.5*barwidth, sh_numbers/hs_numbers, align='center', width=barwidth, label='Sys')
    ax.bar(x+0.5*barwidth, sh_numbers/orig_numbers, align='center', width=barwidth, label='orig')
    ax.set_xticks(x, [name.split('/')[1] for name in names], rotation=45, ha='right')
    ax.axhline(y=1, color='black', linestyle=':', linewidth=2, label='base')
    ax.legend()
    speedup=sh_numbers/hs_numbers
    origup=sh_numbers/orig_numbers
    print(f'{speedup.mean()} {speedup.min()} {speedup.max()}')
    print(f'{origup.mean()} {origup.min()} {origup.max()}')

if __name__ == '__main__':
    draw(plt)
    plt.tight_layout()
    plt.savefig(fig_outfile)

# draw_size_table(names, results, 'bio4_tab.tex')
