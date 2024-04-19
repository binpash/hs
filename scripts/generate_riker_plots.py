import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# create the csv by parsing the output files in ../output/ directory
if (".csv" not in sys.argv[1]):
    print("Data file not specified. Trying to parse the output files in ../report/output/ directory.")

    with open("riker_data_automated.csv", "w") as csv:
        csv.write("benchmark,sh,strace_time,riker_time,hs_time\n")

    benchmarks = ["autoconf", "calc", "coreutils", "llvm", "lsof", "lua", "make", "memcached", "protobuf", "redis", "sqlite", "vim", "xz", "xz-clang"]
    for benchmark in benchmarks.copy():
        try:
            line = f"{benchmark},"
            with open(f'../report/output/{benchmark}/sh_time', 'r') as file:
                lines = file.readlines()
                time = float(lines[0])
                line += f"{time},"
            with open(f'../report/output/{benchmark}/strace_time', 'r') as file:
                lines = file.readlines()
                time = float(lines[0])
                line += f"{time},"
            with open(f'../report/output/{benchmark}/riker_time', 'r') as file:
                lines = file.readlines()
                time = float(lines[0])
                line += f"{time},"
            with open(f'../report/output/{benchmark}/hs_time', 'r') as file:
                lines = file.readlines()
                time = float(lines[0])
                line += f"{time}\n"
            with open("riker_data.csv", "a") as csv:
                csv.write(line)
        except:
            print(f"Error processing {benchmark}")
            benchmarks.remove(benchmark)

    data = pd.read_csv("riker_data.csv").dropna()
    result_filename = sys.argv[1]

else: 
    data = pd.read_csv(sys.argv[1]).dropna()
    result_filename = sys.argv[2]

# Calculate relative execution time compared to sh
data['strace_time'] = data['strace_time'] / data['sh']
data['riker_time'] = data['riker_time'] / data['sh']
data['hs_time'] = data['hs_time'] / data['sh']

# Melt the dataframe to long format for easy plotting with seaborn, excluding sh
data_long = data.melt(id_vars='benchmark', value_vars=['strace_time', 'riker_time', 'hs_time'],
                      var_name='Measurement', value_name='Relative Execution Time to sh')

# Adjusting measurement names for clarity in the legend
data_long['Measurement'] = data_long['Measurement'].map({'strace_time': 'strace', 'riker_time': 'Riker', 'hs_time': 'hs'})

# Increase global font size
plt.rcParams.update({'font.size': 25, 'font.family': 'serif', 'legend.title_fontsize': 25})

# Create the plot
plt.figure(figsize=(16, 10))
barplot = sns.barplot(x='benchmark', y='Relative Execution Time to sh', hue='Measurement', data=data_long, palette='gray')

# Draw a horizontal line at y=1 to represent sh baseline
plt.axhline(y=1, color='black', linestyle='--', label='sh (Baseline)')

# Format y-tick labels to show "times X" with larger font size
plt.gca().set_yticklabels([f'{y:.0f}x' for y in plt.gca().get_yticks()], fontsize=20)

# Customizing the plot with larger fonts
plt.xlabel('', fontsize=25)
plt.ylabel('Relative Execution Time to SH', fontsize=25)
plt.xticks(rotation=45, fontsize=27)
plt.legend(title='', fontsize=20, title_fontsize='25')

plt.tight_layout()
plt.savefig(result_filename, bbox_inches='tight', pad_inches=0.05)
