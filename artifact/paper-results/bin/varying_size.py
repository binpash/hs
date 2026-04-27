#!/usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import numpy as np
# Don't import everything here, I have shadowed functions
from config import get_results, FIG_OUTDIR

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 20})  # Global font size

fig_outfile = FIG_OUTDIR / "varying_size.pdf"

ylim=8



def draw_size_scatter_figure(plt, size_names, sh_numbers, hs_numbers):
    single_x = np.arange(len(size_names))
    x = []
    y = []
    small_x = []
    small_y = []
    for size_i in range(len(sh_numbers)):
        for expr_j in range(len(sh_numbers[size_i])):
            if sh_numbers[size_i][expr_j] > 10:
                x.append(size_i)
                y.append(sh_numbers[size_i][expr_j]/hs_numbers[size_i][expr_j])
            else:
                small_x.append(size_i)
                small_y.append(sh_numbers[size_i][expr_j]/hs_numbers[size_i][expr_j])
    plt.scatter(x, y, color='black', s=20)
    plt.scatter(small_x, small_y, color='red', s=20)
    plt.axhline(y=1, color='black', linestyle=':', linewidth=2, label='Threshold')
    plt.set_xticks(single_x, size_names)
    # Same ylim for all plots
    plt.set_ylim(0, ylim)

    plt.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)


    # plt.set_xlabel('Input sets')
    # plt.set_ylabel('Relative speed up')


def draw_size_boxplot_figure(ax, size_names, sh_numbers, hs_numbers):
    # Compute the relative speedup for each group
    ratios = [
        [sh / hs for sh, hs in zip(sh_numbers[size_idx], hs_numbers[size_idx])]
        for size_idx in range(len(size_names))
    ]

    # Create the box plot
    ax.boxplot(ratios, labels=size_names, patch_artist=True, 
               boxprops=dict(facecolor='lightblue', color='black'),
               medianprops=dict(color='red', linewidth=2),
               whiskerprops=dict(color='black'),
               capprops=dict(color='black'),
               widths=0.6)

    # Add a horizontal line for the baseline (y=1)
    ax.axhline(y=1, color='black', linestyle=':', linewidth=2, label='Baseline')

    # Set labels and title
    # ax.set_ylabel('Relative Speedup')
    # ax.set_xlabel('Input Sets')
    # ax.set_title('Relative Speedup Box Plot for NLP Benchmarks')
    ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)
    # ax.legend(loc='upper right', fontsize=10)

def draw_size_figure(plt, size_names, sh_numbers, hs_numbers):
    x = np.arange(len(size_names))
    sh_numbers = np.array(sh_numbers)
    hs_numbers = np.array(hs_numbers)
    plt.bar(x, sh_numbers/hs_numbers, align='center')
    # plt.set_xlabel('Input sets')
    # plt.set_ylabel('Relative speed up')
    plt.axhline(y=1, color='black', linestyle=':', linewidth=2, label='baseline')
    # for i, value in enumerate(sh_numbers):
    #     plt.text(i, 1 + .02, f"{sh_numbers[i]:.1f}", 
    #          ha='center', va='bottom', color='black', fontsize=10)
    # plt.set_ylim(0, max(sh_numbers/hs_numbers) * 1.08)
    # Same ylim for all plots
    plt.set_ylim(0, ylim)
    for i, value in enumerate(hs_numbers):
        plt.text(i, sh_numbers[i]/hs_numbers[i], f"{sh_numbers[i]:.1f}s/{hs_numbers[i]:.1f}s", 
                 ha='center', va='bottom', color='black', fontsize=8)
    plt.set_xticks(x, size_names)

def bio4_draw(plt):
    names = ['bio4/small', 'bio4/medium', 'bio4/large']
    results = get_results(names)

    sh_values = [results[n][0] for n in names]
    hs_values = [results[n][1] for n in names]

    draw_size_figure(plt, ['S', 'M', 'L'], sh_values, hs_values)

def noaa_draw(plt):
    names = ['max_temp/tiny', 'max_temp/small', 'max_temp/medium', 'max_temp/large']
    results = get_results(names)

    sh_values = [results[n][0] for n in names]
    hs_values = [results[n][1] for n in names]

    draw_size_figure(plt, ['XS', 'S', 'M', 'L'], sh_values, hs_values)

def log_analysis_draw(plt):
    names = ['log-analysis/small', 'log-analysis/medium', 'log-analysis/full']
    results = get_results(names)

    sh_values = [results[n][0] for n in names]
    hs_values = [results[n][1] for n in names]

    draw_size_figure(plt, ['S', 'M', 'L'], sh_values, hs_values)

def combined_draw(ax):
    # Data for Bio4
    bio4_names = ['S', 'M', 'L']
    bio4_results = get_results(['bio4/small', 'bio4/medium', 'bio4/large'])
    bio4_sh_values = [bio4_results[n][0] for n in bio4_results]
    bio4_hs_values = [bio4_results[n][1] for n in bio4_results]
    bio4_ratios = np.array(bio4_sh_values) / np.array(bio4_hs_values)

    # Data for NOAA
    noaa_names = ['XS', 'S', 'M', 'L']
    noaa_results = get_results(['max_temp/tiny', 'max_temp/small', 'max_temp/medium', 'max_temp/large'])
    noaa_sh_values = [noaa_results[n][0] for n in noaa_results]
    noaa_hs_values = [noaa_results[n][1] for n in noaa_results]
    noaa_ratios = np.array(noaa_sh_values) / np.array(noaa_hs_values)

    # Data for Log Analysis
    log_names = ['S', 'M', 'L']
    log_results = get_results(['log-analysis/small', 'log-analysis/medium', 'log-analysis/full'])
    log_sh_values = [log_results[n][0] for n in log_results]
    log_hs_values = [log_results[n][1] for n in log_results]
    log_ratios = np.array(log_sh_values) / np.array(log_hs_values)

    # Combine all data
    all_names = log_names + bio4_names + noaa_names
    all_ratios = np.concatenate([log_ratios, bio4_ratios, noaa_ratios])
    all_labels = ['Log Analysis'] * len(log_names) + ['Bio4'] * len(bio4_names) + ['NOAA'] * len(noaa_names)

    # Create the plot
    x = np.arange(len(all_names))  # x positions for bars
    bar_width = 0.8
    colors = ['skyblue', 'lightgreen', 'salmon']  # Colors for each group

    # Bar plot
    for i, label in enumerate(set(all_labels)):
        idx = [j for j, lbl in enumerate(all_labels) if lbl == label]
        ax.bar(x[idx], all_ratios[idx], width=bar_width, color=colors[i], label=label, edgecolor='black')

    ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.7)

    # Add labels and horizontal baseline
    ax.axhline(y=1, color='black', linestyle=':', linewidth=2, label='Baseline')
    ax.set_xticks(x, all_names)
    # Same ylim for all plots
    ax.set_ylim(0, 3.5)
    ax.set_ylabel('Relative Speedup')
    # ax.set_title('Combined Speedup Comparison')
    ax.set_xlabel('LogAnalysis, Genomics, NOAA')
    ax.legend(loc='upper left', fontsize=14)

    # Add text annotations
    # for i, ratio in enumerate(all_ratios):
    #     ax.text(x[i], ratio + 0.05, f"{ratio:.2f}", ha='center', va='bottom', fontsize=8)



def nlp_draw(plt):
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
    draw_size_boxplot_figure(plt, ['orig', '10×', '100×'], sh_values, hs_values)



# fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 6), constrained_layout=True)

fig = plt.figure(figsize=(10, 4.5))
# gs = GridSpec(1, 4, width_ratios=[1, 1, 1, 2])  # Two columns with different widths
# # gs.update(wspace=0.2)  # Reduce spacing

# # fig.set_constrained_layout(True)


# ax1 = fig.add_subplot(gs[0])
# ax2 = fig.add_subplot(gs[1])
# ax3 = fig.add_subplot(gs[2])
# ax4 = fig.add_subplot(gs[3])

# # ax1 = axes[0, 0]
# # ax2 = axes[0, 1]
# # ax3 = axes[1, 0]
# # ax4 = axes[1, 1]

# log_analysis_draw(ax3)
# ax3.set_xlabel("LogAnalysis")
# bio4_draw(ax1)
# ax1.set_xlabel("Genomics")
# nlp_draw(ax4)
# ax4.set_xlabel("NLP")
# noaa_draw(ax2)
# ax2.set_xlabel("NOAA")

# ax1.set_ylabel('Relative speed up')
# ax2.set_yticklabels([])
# ax3.set_yticklabels([])
# ax4.set_yticklabels([])
# # ax3.set_ylabel('Relative speed up')
# # ax3.set_xlabel('Input sets')
# # ax4.set_xlabel('Input sets')



gs = GridSpec(1, 2, width_ratios=[2, 1])  # Two columns with different widths
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

combined_draw(ax1)
nlp_draw(ax2)
ax2.set_xlabel("NLP")


# fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1, wspace=0.1, hspace=0.1)


plt.tight_layout()



# plt.tight_layout(pad=1.0, w_pad=0.1, h_pad=0.5)

plt.savefig(fig_outfile, dpi=300)
