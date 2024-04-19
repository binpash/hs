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

# Ensure numeric types for 'sh', 'hs (15)', and 'hs(56)' if it exists
data['sh'] = pd.to_numeric(data['sh'], errors='coerce')
data['hs (15)'] = pd.to_numeric(data['hs (15)'], errors='coerce')
data['hs(56)'] = pd.to_numeric(data['hs(56)'], errors='coerce') if 'hs(56)' in data.columns else None

# Drop rows with NaNs in 'sh'
data.dropna(subset=['sh'], inplace=True)

# Calculate the relative speedup for hs (15) and hs (56) compared to sh, if hs(56) exists
data['hs (15)'] = data['sh'] / data['hs (15)']
if 'hs(56)' in data.columns:
    data['hs (56)'] = data['sh'] / data['hs(56)']

# Melt the dataframe to long format for easy plotting with seaborn, excluding sh
value_vars_to_melt = ['hs (15)', 'hs (56)'] if 'hs(56)' in data.columns else ['hs (15)']
data_long = data.melt(id_vars=['Benchmark', 'Benchmark Family'], value_vars=value_vars_to_melt,
                      var_name='Measurement', value_name='Relative Speedup')

# Set global font properties
plt.rcParams.update({'font.size': 14, 'font.family': 'serif'})

# Plotting
fig, axs = plt.subplots(1, 2, figsize=(7, 6), sharey=True)

# Filter data for boxplot and barplot based on 'Benchmark Family'
grouped_data = data_long[data_long['Benchmark Family'] != "BAR"]
bar_data = data_long[data_long['Benchmark Family'] == "BAR"]

# Boxplot for grouped benchmarks with scatter
sns.boxplot(x='Benchmark Family', y='Relative Speedup', hue='Measurement', data=grouped_data, ax=axs[0],
            palette='pastel', showfliers=False)
            # whiskerprops=dict(color="black"), capprops=dict(color="black"),
            # medianprops=dict(color="black"))

# Adding scatter plot with jitter on top of boxplots for individual data points
sns.stripplot(x='Benchmark Family', y='Relative Speedup', hue='Measurement', data=grouped_data, ax=axs[0], dodge=True,
              color='black', size=7, alpha=0.7, jitter=True, legend=False)

axs[0].legend_.remove()  # Remove the legend created by stripplot to avoid duplication
# Barplot for "BAR" benchmarks in grey
sns.barplot(x='Benchmark', y='Relative Speedup', hue='Measurement', data=bar_data, ax=axs[1], palette='pastel')

# Customize plot elements
for ax in axs:
    ax.axhline(y=1, color='black', linestyle='--', label='sh (Baseline)')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45)
    ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.1f}x' if x % 1 == 0.5 else f'{x:.0f}x'))
    ax.legend(title='', fontsize=12)

axs[1].set_ylabel('')  # Remove the ylabel of the second diagram
axs[1].get_legend().remove()  # Remove the legend created by barplot to avoid duplication

axs[0].set_ylabel('Relative Speedup', fontsize=16)

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig(args.output_file, bbox_inches='tight', pad_inches=0.05)
