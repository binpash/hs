import os
import glob
import sys
from matplotlib import pyplot as plt
import pandas as pd
import argparse

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


plt.figure(figsize=(10, 6))
markers = ['o', 'v', '^', '<', '>']
colors = ['0.6', '0.3', '0']
lines = ['-', '--', '-.', ':']

for i, benchmark_name in enumerate(df['benchmark_name'].unique()):
    benchmark_df = df[df['benchmark_name'] == benchmark_name]
    plt.plot(benchmark_df['window'], benchmark_df['hs_base_ratio'], label=benchmark_name, linestyle="-", marker=markers[i % len(markers)], color=colors[i % len(colors)])



# Add dotted line at y=1 to indicate the base performance
plt.axhline(y=1, color='k', linestyle=':', linewidth=2, label='sh time')

plt.xlabel('Window')
plt.ylabel('Relative Time')
plt.legend(title='Benchmark Name')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# Log scale on x-axis (messes up 0 value)
# plt.xscale('log', base=2)  # Corrected log2 scale setting
# plt.gca().xaxis.set_major_formatter(plt.FormatStrFormatter('%d'))

plt.xticks(df['window'].unique())
plt.tight_layout()
plt.savefig(sys.argv[2])
