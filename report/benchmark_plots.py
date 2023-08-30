import matplotlib.pyplot as plt
import scienceplots

# plt.style.use('science')
    
# Plot a comparison of execution times for Bash and Orch.
def plot_benchmark_results(benchmarks, bash_times, orch_times):
    


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
    plt.savefig("out.pdf")
