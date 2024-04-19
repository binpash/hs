import os
import glob
import sys
import pandas as pd
import argparse
import matplotlib.pyplot as plt

# Set global font properties
plt.rcParams.update({'font.size': 14, 'font.family': 'serif'})

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate window plots')
parser.add_argument('input_directory', type=str, help='Path to the input directory')
parser.add_argument('output_file', type=str, help='Path to the output file')
parser.add_argument('--benchmarks', type=str, nargs='+', help='List of benchmarks to plot')
args = parser.parse_args()

csv_files = glob.glob(os.path.join(sys.argv[1], "*.csv"))
csv_files = sorted(csv_files, key=lambda x: int(x.split("_w")[1].split(".")[0]))

benchmark_results = []

for csv_file in csv_files:
    df_temp = pd.read_csv(csv_file)
    window = int(csv_file.split("_w")[1].split(".")[0])  # Extracting window number from filename
    for _, row in df_temp.iterrows():
        if args.benchmarks is None or row["benchmark_name"] in args.benchmarks:
            benchmark_results.append({
                "benchmark_name": row["benchmark_name"],
                "window": window,
            "hs_time": row["hs_time"],
            "base_time": row["sh_time"] if "w0" in csv_file else None  # Base time is sh_time from results_w0.csv
        })

df = pd.DataFrame(benchmark_results)

# Fill in base_time for all records based on benchmark_name matching
df['base_time'] = df.groupby('benchmark_name')['base_time'].transform(lambda x: x.ffill().bfill())
# Calculate hs_time / base_time ratio
df['hs_base_ratio'] = df['hs_time'] / df['base_time']
# Calculate relative speedup as base_time / hs_time
df['relative_speedup'] = df['base_time'] / df['hs_time']



plt.figure(figsize=(10, 6))
markers = ['o', 'v', '^', '<', '>', '*', "s"]
colors = ['0.6', '0.3', '0']
lines = ['-', '--', '-.', ':']

# for i, benchmark_name in enumerate(df['benchmark_name'].unique()):
#     benchmark_df = df[df['benchmark_name'] == benchmark_name]
#     plt.plot(benchmark_df['window'], benchmark_df['hs_base_ratio'], label=benchmark_name, linestyle="-", marker=markers[i % len(markers)], color=colors[i % len(colors)])

# Relative speedup
for i, benchmark_name in enumerate(df['benchmark_name'].unique()):
    benchmark_df = df[df['benchmark_name'] == benchmark_name]
    plt.plot(benchmark_df['window'], benchmark_df['relative_speedup'], label=benchmark_name, linestyle="-", marker=markers[i % len(markers)], color=colors[i % len(colors)])


# Add dotted line at y=1 to indicate the base performance
plt.axhline(y=1, color='k', linestyle=':', linewidth=2, label='Base Performance')

# Update y-axis label to reflect the change to relative speedup
plt.ylabel('Relative Speedup', fontsize=16, fontfamily='serif')

# Set axis labels with specific font properties
plt.xlabel('Window', fontsize=16, fontfamily='serif')

plt.legend(title='', fontsize='10')
plt.grid(True, which='both', linestyle='--', linewidth=0.3)

# Log scale on x-axis (messes up 0 value)
# plt.xscale('log', base=2)  # Corrected log2 scale setting
# plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))
# Set x-axis and y-axis tick label properties

# Get current y-axis tick labels
current_yticks = plt.gca().get_yticks()

# Format y-axis tick labels
formatted_yticklabels = [f"{label.round(2)}x" for label in current_yticks]

# Set formatted y-axis tick labels with specific font properties and tilt them
plt.yticks(ticks=current_yticks, labels=formatted_yticklabels, fontsize=10, fontfamily='serif', rotation=45)


# Set formatted y-axis tick labels with specific font properties
plt.yticks(ticks=current_yticks, labels=formatted_yticklabels, fontsize=14, fontfamily='serif')


plt.xticks(fontsize=14, fontfamily='serif')
plt.yticks(fontsize=14, fontfamily='serif')
plt.xticks(df['window'].unique())
plt.tight_layout()

plt.savefig(sys.argv[2], bbox_inches='tight', pad_inches=0.05)
