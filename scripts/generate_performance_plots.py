import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate box and bar plots for benchmarks.')
parser.add_argument('input_directory', type=str, help='Path to the input directory containing the CSV file')
parser.add_argument('output_file', type=str, help='Path to the output PDF file')
args = parser.parse_args()

# Construct the path to the data file
data_file_path = os.path.join(args.input_directory, 'data.csv')

# Read the data
data = pd.read_csv(data_file_path)

# Ensure numeric types for 'sh' and 'hs (15)' columns
data['sh'] = pd.to_numeric(data['sh'], errors='coerce')
data['hs (15)'] = pd.to_numeric(data['hs (15)'], errors='coerce')

# Drop rows with NaNs created by conversion errors or originally missing values
data.dropna(subset=['sh', 'hs (15)'], inplace=True)

# Calculate the relative speedup
data['Relative Speedup'] = data['sh'] / data['hs (15)']

# Split data for boxplot and barplot
grouped_data = data[data['Benchmark Family'] != "BAR"]
bar_benchmarks = data[data['Benchmark Family'] == "BAR"]

# Set global font properties
plt.rcParams.update({'font.size': 14, 'font.family': 'serif'})

# Plotting
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)

# Boxplot for grouped benchmarks with scatter
sns.boxplot(x='Benchmark Family', y='Relative Speedup', data=grouped_data, width=0.5, ax=axs[0],
            boxprops=dict(facecolor="lightgrey", edgecolor="black"), whiskerprops=dict(color="black"),
            capprops=dict(color="black"), medianprops=dict(color="black"))

# Scatter plot with larger, darker color dots for better visibility
sns.stripplot(x='Benchmark Family', y='Relative Speedup', data=grouped_data, jitter=True, ax=axs[0], color='black', size=7, alpha=0.7)

# Reference line at y=1, indicating the base performance
axs[0].axhline(y=1, color='black', linestyle='--')
axs[0].set_xlabel('')
axs[0].set_ylabel('Relative Speedup', fontsize=16)
axs[0].tick_params(axis='x', rotation=45)

# Barplot for "BAR" benchmarks in grey
sns.barplot(x='Benchmark', y='Relative Speedup', data=bar_benchmarks, ax=axs[1], color='grey')
axs[1].set_xlabel('')
axs[1].set_ylabel('')
axs[1].axhline(y=1, color='k', linestyle='--')
axs[1].tick_params(axis='x', rotation=45)

# Custom formatter for y-tick labels to add "x"
axs[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}x'))
axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}x'))

# Shared X-axis label
# fig.text(0.5, 0.04, 'Benchmark Categories', ha='center', fontsize=16)

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig(args.output_file, bbox_inches='tight', pad_inches=0.05)
