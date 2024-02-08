import os
import matplotlib.pyplot as plt

# Set the plotting style if desired
# plt.style.use('ggplot')  # Example: ggplot style

# Creates a bar chart on the given axis.
def create_bar_chart(ax, labels, data, bar_width, position, color, label):
    return ax.bar([p + position for p in range(len(data))], data, bar_width, label=label, color=color)

# Configures the axes properties.
def setup_ax(ax, xlabel, ylabel, title, xticks, xticklabels):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, rotation=45, ha='right')

# Saves the current plot to the specified directory.
def save_plot(output_dir, filename):
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{filename}.pdf"))

# Plots a comparison of execution times for Bash and hs.
def plot_benchmark_times_combined(benchmarks, bash_times, orch_times, output_dir, filename):
    fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.35

    create_bar_chart(ax, benchmarks, bash_times, bar_width, 0, 'b', 'Bash')
    create_bar_chart(ax, benchmarks, orch_times, bar_width, bar_width, 'r', 'hs')

    setup_ax(ax, 'Benchmarks', 'Execution Time (s)', 'Execution Time Comparison: Bash vs hs',
             [i + bar_width / 2 for i in range(len(benchmarks))], benchmarks)
    ax.legend()

    save_plot(output_dir, filename)

# Plots individual comparison charts for each benchmark.
def plot_benchmark_times_individual(benchmarks, bash_times, orch_times, output_dir, filename):
    num_benchmarks = len(benchmarks)
    fig, axes = plt.subplots(num_benchmarks, 1, figsize=(10, 6 * num_benchmarks), squeeze=False)
    
    for ax, benchmark, bash_time, orch_time in zip(axes.flatten(), benchmarks, bash_times, orch_times):
        labels = ['Bash', 'hs']
        times = [bash_time, orch_time]
        create_bar_chart(ax, labels, times, 0.2, 0, 'b', 'Bash')
        create_bar_chart(ax, labels, times, 0.2, 0.2, 'r', 'hs')

        setup_ax(ax, '', 'Execution Time (s)', f'Execution Time Comparison for {benchmark}', range(len(labels)), labels)

    save_plot(output_dir, filename)

# Plots a Gantt chart of activities.
def plot_gantt(activities, output_dir, filename, simple=False):
    if simple:
        activities = [activity for activity in activities if activity[0].startswith("RunNode,") or activity[0] == "Wait"]

    fig_height = max(5, len(activities) * 0.3)
    fig, ax = plt.subplots(figsize=(15, fig_height))

    activities.sort(key=lambda x: x[1])
    bar_height = 0.8
    gap = 0.2

    for index, (action, start_time, duration) in enumerate(activities):
        ax.broken_barh([(start_time, duration)], (index * (bar_height + gap), bar_height), facecolors='blue')
        ax.text(start_time + duration / 2, index * (bar_height + gap) + bar_height / 2, action, 
                ha='center', va='center', fontsize=6, color='white')

    setup_ax(ax, 'Time (ms)', '', f'Gantt Chart of {filename.strip("_gantt.pdf")}', [], [])
    ax.set_yticks([i * (bar_height + gap) + bar_height / 2 for i in range(len(activities))])
    ax.set_yticklabels([activity[0] for activity in activities], fontsize=8)
    ax.grid(True)

    save_plot(output_dir, filename)
