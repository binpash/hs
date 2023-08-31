import os
import matplotlib.pyplot as plt
# import scienceplots

# plt.style.use('science')
    
# Plot a comparison of execution times for Bash and hs.
def plot_benchmark_times_combined(benchmarks, bash_times, orch_times, output_dir, filename):
    fig, ax = plt.subplots(figsize=(10,6))
    
    # Define bar width and positions
    bar_width = 0.35
    index = range(len(benchmarks))
    
    bar1 = ax.bar(index, bash_times, bar_width, label='bash', color='b')
    bar2 = ax.bar([i+bar_width for i in index], orch_times, bar_width, label='hs', color='r')
    
    ax.set_xlabel('Benchmarks')
    ax.set_ylabel('Execution Time (s)')
    ax.set_title('Execution Time Comparison: Bash vs orch')
    ax.set_xticks([i + bar_width/2 for i in index])
    ax.set_xticklabels(benchmarks)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{filename}.pdf"))

def plot_benchmark_times_individual(benchmarks, bash_times, orch_times, output_dir, filename):
    num_benchmarks = len(benchmarks)
    fig, axes = plt.subplots(num_benchmarks, 1, figsize=(10, 6*num_benchmarks))
    # Check if only one benchmark, else wrap axes in a list
    if num_benchmarks == 1:
        axes = [axes]
    for ax, benchmark, bash_time, pash_time in zip(axes, benchmarks, bash_times, orch_times):
        bar_width = 0.2
        labels = ['Bash', 'hs']
        times = [bash_time, pash_time]
        ax.bar(labels, times, width=bar_width, color=['b', 'r'])
        ax.set_ylabel('Execution Time (s)')
        ax.set_title(f'Execution Time Comparison for {benchmark}: Bash vs hs')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{filename}.pdf"))