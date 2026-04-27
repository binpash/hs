# Assumes CSV file with the following columns:
# - benchmark: Name of the benchmark
# - sub-benchmark: Name of the sub-benchmark
# - sh: sh time
# - hs: hs time

# For the ones that go to the barplot, the 'sub-benchmark' should be 'BAR'
# For the other ones, the 'sub-benchmark' should be the name of the benchmark


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

import cpu_time
from config import FIG_OUTDIR, DATA_DIR

scatter_fig_outfile = FIG_OUTDIR / "scatter_performance_original_teraseq.pdf"
input_file = DATA_DIR / "final_eval_original_teraseq.csv"

# sns.set_theme(style='ticks')

# Parse command line arguments
# parser = argparse.ArgumentParser(description='Generate box and bar plots for benchmarks.')
# args = parser.parse_args()

# Read the data
data = pd.read_csv(input_file)




## Set subbenchmark
# for i in 
data[['benchmark', 'sub-benchmark']] = data['benchmark'].str.split('/', expand=True)
# print(data['sub-benchmark'])

# Ensure numeric types for 'sh' and 'hs'
for run in range(1, 5):
    sh_column = f'sh_time{run}'
    hs_column = f'hs_time{run}'
    data[sh_column] = pd.to_numeric(data[sh_column], errors='coerce')
    data[hs_column] = pd.to_numeric(data[hs_column], errors='coerce')

    # Drop rows with NaNs in 'sh'
    # data.dropna(subset=['sh'], inplace=True)

    # Save 'hs' execution time before computing Speedup vs sh
    hs_exec_time_col = f'hs_exec_time{run}'
    data[hs_exec_time_col] = data[hs_column]

    # Calculate the Speedup vs sh for 'hs' compared to 'sh'
    data[hs_column] = data[sh_column] / data[hs_column]

# Melt the dataframe to long format for plotting, including 'sh' and 'hs_exec_time'
value_vars_to_melt = ['hs_time1']
data_long = data.melt(
    id_vars=['benchmark', 
             'sub-benchmark', 
             'sh_time1', 
             'hs_exec_time1'],
    value_vars=value_vars_to_melt,
    var_name='Measurement',
    value_name='Speedup vs sh'
)
# print(data_long)

# Set global font properties
# plt.rcParams.update({'font.size': 8, 'font.family': 'sans-serif'})

plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'font.size': 12})  # Further reduce global font size


# Plotting
fig = plt.figure(figsize=(8, 2.9))  # Make the first plot even smaller
# Create a GridSpec with width ratios 1:2
gs = GridSpec(1, 2, width_ratios=[1,1.5])  # The last 0.1 is to adjust spacing
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])

# Filter data for boxplot and barplot based on 'sub-benchmark'
# grouped_data = data_long[data_long['sub-benchmark'] != "BAR"]
# bar_data = data_long[data_long['sub-benchmark'] == "BAR"]

bar_rows = ['bio4',
            'bus-analytics',
            'log-analysis',
            'max_temp',
            'sklearn_large',
            'web-index',
            'unix_50']

box_rows = ['dgsh',
            'nlp100x',
            'teraseq']

bar_data_df = data_long[data_long['benchmark'].isin(bar_rows)]
grouped_data_df = data_long[data_long['benchmark'].isin(box_rows)]

# Keep only relevant benchmarks for bars
relevant_bar_benchmarks = [('bio4','large'),
                           ('bus-analytics', 'full-10G'),
                           ('log-analysis', 'full'),
                           ('sklearn_large', None),
                           ('web-index', 'web-index-100m'),
                           ('unix_50', 'full100m'),
                           ('max_temp', 'large')]

mask = bar_data_df.apply(lambda row: (row['benchmark'], row['sub-benchmark']) in relevant_bar_benchmarks, 
                         axis=1)

# Filter the rows

bar_data_df = bar_data_df[mask]

relevant_dgsh_subbenchmarks = ['1-1000x',
                                '2',
                                '3',
                                '4',
                                '5-1000x',
                                '6-1000x',
                                '7-1000x',
                                '8-1000x',
                                '9',
                                '17-1000x',
                                '18',
                                ]
grouped_data_df = grouped_data_df[(grouped_data_df['benchmark'] != 'dgsh') | 
                                  (grouped_data_df['sub-benchmark'].isin(relevant_dgsh_subbenchmarks))]


## TODO: Come up with pretty names

sh_column = 'sh_time1'
hs_exec_time_col = 'hs_exec_time1'


# Split the data based on 'sh' value
data_sh_ge_10 = grouped_data_df[grouped_data_df[sh_column] >= 10]  # 'sh' >= 10
data_sh_lt_10 = grouped_data_df[grouped_data_df[sh_column] < 10]   # 'sh' < 10

print(bar_data_df)
print(grouped_data_df)


benchmark_groups = grouped_data_df.groupby('benchmark')['Speedup vs sh']

# Prepare data for boxplot
data_for_boxplot = [group.tolist() for _name, group in benchmark_groups]

# Plot

grouped_data = grouped_data_df.values.tolist()
print(grouped_data)

ax1.boxplot(data_for_boxplot, 
            labels=benchmark_groups.groups.keys(),
            patch_artist=True, 
            boxprops=dict(facecolor='lightblue', color='black'),
            medianprops=dict(color='red', linewidth=2),
            whiskerprops=dict(color='black'),
            capprops=dict(color='black'),
            widths=0.6)

# ax1.set_xlabel("Benchmark")
# ax1.set_ylabel("Speedup vs sh")
# ax1.xticks(rotation=45)  # Rotate x-axis labels if needed


# Boxplot for grouped benchmarks
# sns.boxplot(
#     x='sub-benchmark',
#     y='Speedup vs sh',
#     hue='Measurement',
#     data=grouped_data,
#     ax=ax1,
#     palette='pastel',
#     showfliers=False
# )
# Scatter plot for 'sh' >= 10 (blue dots)
# sns.stripplot(
#     x='sub-benchmark',
#     y='Speedup vs sh',
#     hue='Measurement',
#     data=data_sh_ge_10,
#     palette=['blue'],
#     ax=ax1,
#     dodge=True,
#     size=7,
#     alpha=1,
#     jitter=True,
#     legend=False
# )




# Remove duplicate legend entries
# ax1.legend_.remove()

# # Overlay red dots for 'sh' < 10 with jitter
# # Compute x positions
# sub_benchmark_order = grouped_data_df['sub-benchmark'].unique()
# sub_benchmark_map = {name: i for i, name in enumerate(sub_benchmark_order)}
# measurement_order = grouped_data_df['Measurement'].unique()
# n_measurements = len(measurement_order)
# dodge_amount = 0.8 / n_measurements
# measurement_offsets = np.linspace(
#     -0.4 + dodge_amount / 2,
#     0.4 - dodge_amount / 2,
#     n_measurements
# )
# measurement_offset_map = {
#     measurement: offset for measurement, offset in zip(measurement_order, measurement_offsets)
# }

# # Calculate x positions for red dots
# x_positions = data_sh_lt_10.apply(
#     lambda row: sub_benchmark_map[row['sub-benchmark']] +
#     measurement_offset_map[row['Measurement']],
#     axis=1
# )

# # Add jitter to x positions
# jitter_amount = dodge_amount / 5  # Adjust the jitter amount as needed
# jitter = np.random.uniform(-jitter_amount, jitter_amount, size=len(x_positions))
# x_positions += jitter

# y_positions = data_sh_lt_10['Speedup vs sh']

# # Plot red dots with jitter
# ax1.scatter(x_positions, y_positions, color='red', s=30, zorder=10)

# Group 'bar_data' to get one data point per bar
bar_data_grouped = bar_data_df.groupby(['benchmark', 'Measurement']).agg({
    'Speedup vs sh': 'mean',
    hs_exec_time_col: 'mean'
}).reset_index()

# Barplot for "BAR" benchmarks
sns.barplot(
    x='benchmark',
    y='Speedup vs sh',
    hue='Measurement',
    data=bar_data_grouped,
    ax=ax2,
    palette='pastel',
    ci=None
)

# Annotate bars with hs execution time
measurement_order = bar_data_grouped['Measurement'].unique()

# for container, measurement in zip(ax2.containers, measurement_order):
#     # Get the data for this measurement
#     data_subset = bar_data_grouped[bar_data_grouped['Measurement'] == measurement]
#     for bar, (_, row) in zip(container, data_subset.iterrows()):
#         x = bar.get_x() + bar.get_width() / 2
#         y = bar.get_height()
#         hs_time = row['hs_exec_time']
#         ax2.text(x, y, f'{hs_time:.0f}s', ha='center', va='bottom', fontsize=8, rotation=90)

# Customize plot elements
y_ticks = np.array([0.125, 0.25, 0.5, 1, 2, 4, 8])
y_tick_labels = ['0.125×', '0.25×', '0.5×', '1×', '2×', '4×', '8×']

# Set y-scale and ticks for both axes
for ax in [ax1, ax2]:
    ax.set_yscale('log', base=2)
    ax.set_ylim([0.125, 8])  # Adjust the limits to include all ticks
    ax.axhline(y=1, color='black', linestyle='--', label='sh (Baseline)')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45)
    # Add light dashed lines at specified ticks (excluding y=1)
    for y in y_ticks:
        if y != 1:
            ax.axhline(y=y, color='gray', linestyle='--', linewidth=0.5, zorder=0)

# Set y-ticks and labels for left plot (ax1)
ax1.set_yticks(y_ticks)
ax1.set_yticklabels(y_tick_labels)
ax1.set_ylabel('Relative performance vs sh')

# Remove y-ticks and labels from right plot (ax2)
ax2.set_yticks(y_ticks)
ax2.set_yticklabels([])
ax2.tick_params(axis='y', which='both', left=False, labelleft=False)
ax2.set_ylabel('')

# Remove duplicate legend
ax2.get_legend().remove()

# Align all x-axis labels at the right-side of the text
for ax in [ax1, ax2]:
    for label in ax.get_xticklabels():
        label.set_horizontalalignment('right')

plt.tight_layout(rect=[0, 0.05, 1, 1])
# plt.savefig(args.output_file, bbox_inches='tight', pad_inches=0.05)


all_data = pd.concat([bar_data_df, grouped_data_df], axis=0)

fig, (ax, ax_misspec) = plt.subplots(1, 2, figsize=(14, 3.3), width_ratios=[3, 1])  # Make scatter plot smaller

# Define unique markers for each benchmark
markers = ['o', 's', '^', 'D', 'P', '*', '<', 'v', '>', 'h']  # Example markers
benchmark_groups = all_data['benchmark'].unique()
marker_map = {benchmark: markers[i % len(markers)] for i, benchmark in enumerate(benchmark_groups)}

order = ['teraseq', 'bio4', 'sklearn_large', 'dgsh', 'nlp100x', 'max_temp',
         'unix_50', 'bus-analytics', 'log-analysis', 'web-index']

pretty_bench_labels = {
    'teraseq': 'TERA-Seq',
    'bio4': 'Genomics',
    'sklearn_large': 'SkLearnLarge',
    'dgsh': 'DGSH',
    'nlp100x': 'NLP',
    'max_temp': 'NOAA',
    'unix_50': 'Unix50',
    'bus-analytics': 'COVID-mts',
    'log-analysis': 'LogAnalysis',
    'web-index': 'WebIndex',
}

colors = [
    '#1f77b4',  # muted blue
    '#ff7f0e',  # safety orange
    '#2ca02c',  # cooked asparagus green
    '#d62728',  # brick red
    '#9467bd',  # muted purple
    '#8c564b',  # chestnut brown
    '#e377c2',  # raspberry yogurt pink
    '#7f7f7f',  # middle gray
    '#bcbd22',  # curry yellow-green
    '#17becf',  # blue-teal
    '#aec7e8'   # light blue (good for lighter elements)
]

colormaps = {b: c for b, c in zip(pretty_bench_labels.keys(), colors)}
# Plot the scatter plot

for benchmark in sorted(benchmark_groups, key=lambda x: order.index(x)):
    subset = all_data[all_data['benchmark'] == benchmark]
    ax.scatter(
        subset['Speedup vs sh'],
        subset[sh_column],
        label=pretty_bench_labels[benchmark],
        marker=marker_map[benchmark],
        s=100,  # Reduced size from 200
        alpha=0.8,
        c=colormaps[benchmark]
    )

below_ten = Rectangle(
    (0, 0),  # Bottom-left corner (x, y)
    1,          # Width of the square
    10,         # Height of the square
    # color='gray', alpha=0.3,  # Gray color with transparency
    # edgecolor='black', linewidth=1.5  # Optional border styling
    color='none', edgecolor='black', linewidth=1.5,
    hatch='//',  # Example texture pattern: slashes
    alpha=0.3    # Transparency for the texture
)
ax.add_patch(below_ten)

sequential = Rectangle(
    (0.9, 0),  # Bottom-left corner (x, y)
    0.2,          # Width of the square
    1000000,         # Height of the square
    # color='gray', alpha=0.3,  # Gray color with transparency
    # edgecolor='black', linewidth=1.5  # Optional border styling
    # color='red', 
    color='none',
    edgecolor='red', linewidth=1.5,
    hatch='o',  # Example texture pattern: slashes
    alpha=0.3    # Transparency for the texture
)
ax.add_patch(sequential)

names, count_overhead, time_overhead = cpu_time.read_logs()
x = np.array(range(len(names)))
print((100*time_overhead/(time_overhead+1)).mean())
ax_misspec.barh(x, 100*time_overhead/(time_overhead+1), color=colors, linewidth=1, edgecolor='black')

# Map names from read_logs() to benchmark names in marker_map
name_to_benchmark = {
    'teraseq': 'teraseq',
    'bio4': 'bio4',
    'sklearn': 'sklearn_large',  # Map sklearn to sklearn_large
    'sklearn_large': 'sklearn_large',
    'dgsh': 'dgsh',
    'max_temp': 'max_temp',
    'nlp': 'nlp100x',  # Map nlp to nlp100x
    'nlp10x': 'nlp100x',
    'nlp100x': 'nlp100x',
    'unix_50': 'unix_50',
    'bus-analytics': 'bus-analytics',
    'log-analysis': 'log-analysis',
    'web-index': 'web-index',
}

for i in range(len(x)):
    benchmark_name = name_to_benchmark.get(names[i], names[i])
    if benchmark_name in marker_map:
        ax_misspec.plot((100*time_overhead/(time_overhead+1))[i]+2, i, marker=marker_map[benchmark_name])
    else:
        # Fallback to a default marker if not found
        ax_misspec.plot((100*time_overhead/(time_overhead+1))[i]+2, i, marker='o')
ax_misspec.set_xlabel('Misspeculation rate (%)')
ax_misspec.set_xticks([0, 20, 40, 60])
ax_misspec.set_yticks(x)
ax_misspec.set_ylim(-0.5, len(x)-0.5)
ax_misspec.set_yticklabels([])
ax_misspec.invert_yaxis()
ax_misspec.set_xlim(0, 60)  # Changed from 100 to 60
ax_misspec.grid(axis='x', linestyle='--', linewidth=1, alpha=0.7)

ax.set_yscale('log')
ax.axvline(x=1, color='black', linestyle='--', linewidth=1, alpha=0.7, label='Baseline')
ax.set_ylabel('bash time (s)')
ax.set_xlim(0, 11)
ax.set_ylim(0, 100000)
ax.set_xlabel('Speedup vs bash')
ax.set_xticks(np.arange(0, 11, 1))
ax.legend(
    title="Benchmark",
    loc='best',
    fontsize=9,
    markerscale=0.7,
    borderpad=0.2,
    labelspacing=0.3,
    handletextpad=0.47,
    borderaxespad=0.27,
    columnspacing=0.6
)
ax.grid(linestyle='--', alpha=0.5, linewidth=1)
# # Add grid, labels, legend, and title
# plt.yscale('log')
# plt.axvline(x=1, color='black', linestyle='--', linewidth=1, alpha=0.7, label='Baseline')
# # plt.axvline(x=1, color='black', linestyle='--', linewidth=1, alpha=0.7, label='Baseline')
# plt.ylabel('bash time (s)')
# plt.xlim(-0.3, 9)
# plt.ylim(0, 100000)
# plt.xlabel('Speedup vs bash')
# plt.xticks(np.arange(0, 9, 1))
# # plt.title('Scatter Plot of Benchmarks', fontsize=14)
# plt.legend(title="Benchmark", loc='best',fontsize=16)
# plt.grid(linestyle='--', alpha=0.5)
# Show Plot
plt.tight_layout()
# plt.show()
plt.savefig(scatter_fig_outfile, bbox_inches='tight', pad_inches=0.05)
