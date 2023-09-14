import subprocess
import time
import json
import os
from benchmark_plots import *
import logging
import difflib
import argparse
import csv



# Setting and exporting environment variables (same as tests for now).
# This will change in the future.
os.environ['ORCH_TOP'] = os.environ.get('ORCH_TOP', subprocess.check_output(['git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']).decode('utf-8').strip())
os.environ['WORKING_DIR'] = os.path.join(os.environ['ORCH_TOP'], 'report')
os.environ['TEST_SCRIPT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'benchmarks')
os.environ['RESOURCE_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'resources')
os.environ['PASH_TOP'] = os.path.join(os.environ['ORCH_TOP'], 'deps', 'pash')
os.environ['PASH_SPEC_TOP'] = os.path.join(os.environ['ORCH_TOP'])

BASH_COMMAND = "/bin/bash"
ORCH_COMMAND = os.path.join(os.environ['ORCH_TOP'], 'pash-spec.sh')
REPORT_OUTPUT_DIR = os.path.join(os.environ['WORKING_DIR'], 'report_output')


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark and report interface for a system.")
    parser.add_argument('--no-plots', action='store_true', help="Do not print plots.")
    parser.add_argument('--no-logs', action='store_true', help="Do not save log files.")
    parser.add_argument('--csv-output', action='store_true', help="Save results in CSV format.")
    return parser.parse_args()


def save_log_data(log_data, output_dir, filename):
    if args.no_logs:
        return
    with open(os.path.join(output_dir, filename), 'w') as f:
        f.write(log_data)


def parse_logs_into_activities(log_data):
    info_lines = [line.replace("INFO:root:>|", "").split("|") for line in log_data.split("\n") if line.startswith("INFO:root:>|")]
    # Define a regex pattern to extract data from the log lines
    pattern = r">\|(?P<activity>[\w\-,]+)\|Time from start:(?P<start_time>[\d\.]+)ms"
    step_time_pattern = r"Step time:(?P<step_time>[\d\.]+)ms"

    activities = []
    
    for line in info_lines:
        if len(line) == 4:
            activity = line[1]
            end_time = float(line[2].split(":")[1].rstrip("ms"))
            step_time = float(line[3].split(":")[1].rstrip("ms"))
            start_time = end_time - step_time
            activities.append((activity, start_time, step_time))
    return activities

def replace_with_env_var(input_string):
    format_args = {
        "TEST_SCRIPT_DIR": os.environ.get("TEST_SCRIPT_DIR", os.getcwd()),
        "RESOURCE_DIR": os.environ.get("RESOURCE_DIR", os.getcwd())
    }
    replaced_string = input_string.format(**format_args)
    return replaced_string

def run_pre_execution_command(command, working_dir=os.getcwd()):
    print("Running pre-execution command:", command)
    process = subprocess.Popen(command, cwd=working_dir)
    process.wait()
    return process.returncode

def run_command(command, working_dir=os.getcwd()):
    print("Running (and timing) command: ", " ".join(command))
    start_time = time.time()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir)
    stdout, stderr = process.communicate()
    end_time = time.time()
    return (end_time - start_time, stdout.decode('utf-8'), stderr.decode('utf-8'))

def run_command_with_orch(command, orch_args, working_dir=os.getcwd()):
    print("Running (and timing) command with orch: ", " ".join(command))
    start_time = time.time()
    process = subprocess.Popen([ORCH_COMMAND, orch_args] + command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir, env=os.environ)
    stdout, stderr = process.communicate()
    end_time = time.time()
    return (end_time - start_time, stdout.decode('utf-8'), stderr.decode('utf-8'))

def compare_results(bash_output, orch_output):
    
    bash_lines = bash_output.splitlines()
    orch_lines = orch_output.splitlines()
    # Compare lines
    d = difflib.ndiff(bash_lines, orch_lines)
    return [diff for diff in d if diff.startswith('- ') or diff.startswith('+ ')]


def print_results(benchmark_name, bash_time, orch_time, diff_lines, diff_percentage):
    if orch_time < bash_time:
            comparison_result = f"hs is {round(diff_percentage/100, 1)}x ({diff_percentage:.2f}%) faster than Bash"
    else:
        comparison_result = f"hs is {round(diff_percentage/100, 1)}x ({diff_percentage:.2f}%) slower than Bash"
    print("-" * 40)
    print(f"Results for benchmark:  {benchmark_name}")
    print(f"Bash Execution Time:    {round(bash_time, 3)}s")
    print(f"hs Execution Time:      {round(orch_time, 3)}s")
    print(f"Valid:                  {'Yes' if len(diff_lines) == 0 else 'No - see below'}")
    if len(diff_lines) > 0:
        for line in diff_lines:
            print(line)
        print("-" * 40)
    print(comparison_result)
    print()
    if args.csv_output:
        csv_filename = os.path.join(REPORT_OUTPUT_DIR, f"results.csv")
        with open(csv_filename, 'a') as csv_file:
            writer = csv.writer(csv_file)
            valid = 'Yes' if len(diff_lines) == 0 else 'No'
            writer.writerow([benchmark_name, bash_time, orch_time, valid, comparison_result])


def print_exec_time_for_cmds(orch_outpt, benchmark_name):
    # Split the log into lines and filter the relevant ones
    relevant_lines = [line.replace("INFO:root:>|PartialOrder|RunNode,", "") for line in orch_outpt.split("\n") if line.startswith("INFO:root:>|PartialOrder|RunNode,") and "Step time:" in line]
    # Extract lines with RunNode commands and their step times
    node_and_times = [(int(line.split("|")[0]), float(line.split("|")[1].split(":")[1][:-2]), float(line.split("|")[2].split(":")[1][:-2])) for line in relevant_lines]

    # Total number of times a RunNode command was executed
    total_run_node_commands = len(node_and_times)
    
    # Total time of all RunNode commands
    total_time = sum([entry[2] for entry in node_and_times])
    
    # Extract and sum the total time of the step per node
    node_times = {}
    node_distinct_times = {}
    counts = {}
    for node, _, time in node_and_times:
        if node in node_times:
            node_times[node] += time
            node_distinct_times[node].append(time)
            counts[node] += 1
        else:
            node_times[node] = time
            node_distinct_times[node] = [time]
            counts[node] = 1
    
    time_lost_per_node = {node: sum(node_distinct_times[node]) - node_distinct_times[node][-1] for node in node_times}

    print("-" * 40)
    print(f"Total number of times a RunNode command was executed: {total_run_node_commands}")
    print(f"Total time of all RunNode commands: {total_time:.3f}ms")
    print("\nTotal execution time per node:")
    for node, time_lost in sorted(time_lost_per_node.items(), key=lambda x: x[1], reverse=True):
        print(f"{node:2d}: {node_times[node]:.3f}ms ({counts[node]} times) | Avg: {sum(node_distinct_times[node])/len(node_distinct_times[node]):.3f}ms | {node_distinct_times[node]} | Time lost: {time_lost:.3f}ms")
    print("-" * 40)
    print(f"Total time lost: {sum(time_lost_per_node.values()):.02f}ms")
    print("=" * 100)
    
    if args.csv_output:
        csv_filename = os.path.join(REPORT_OUTPUT_DIR, f"{benchmark_name}_execution_times.csv")
        with open(csv_filename, 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Node", "Time (ms)", "Execution Count", "Average Time (ms)", "Distinct Times", "Time Lost (ms)"])
            for node, time_lost in sorted(time_lost_per_node.items(), key=lambda x: x[1], reverse=True):
                writer.writerow([node, node_times[node], counts[node], sum(node_distinct_times[node])/len(node_distinct_times[node]), node_distinct_times[node], time_lost])



def export_env_vars(env_vars):
    for env_var in env_vars:
        lhs, rhs = env_var.split("=")
        rhs = replace_with_env_var(rhs)
        os.environ[lhs] = rhs


def main():
    
    # Load benchmark configurations
    with open(os.path.join(os.environ.get('WORKING_DIR'), 'benchmark_config.json'), 'r') as f:
        benchmarks_config = json.load(f)
        
    bash_times = []
    orch_times = []
    
    # Create output dir for reports
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    
    if args.csv_output:
        csv_filename = os.path.join(REPORT_OUTPUT_DIR, f"results.csv")
        with open(csv_filename, 'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Benchmark", "Bash Execution Time", "hs Execution Time", "Valid", "Comparison"])

    for benchmark in benchmarks_config:
        print("=" * 100)
        # Set up preferred environment
        export_env_vars(benchmark.get('env', {}))
        # Create resource dir if non-existent
        os.makedirs(os.environ.get('RESOURCE_DIR'), exist_ok=True)
        # Run pre-execution commands
        for pre_command in benchmark.get('pre_execution_script', []):
            print(f"{pre_command}")
            split_pre_command = replace_with_env_var(pre_command).split(" ")
            run_pre_execution_command(split_pre_command, os.environ.get('RESOURCE_DIR'))

        working_dir = replace_with_env_var(benchmark.get('working_dir', os.environ.get('TEST_SCRIPT_DIR')))
        
        bash_cmd_str = [BASH_COMMAND] + replace_with_env_var(benchmark['command']).split(" ")
        bash_time, bash_output, _bash_error = run_command(bash_cmd_str, working_dir)
        orch_cmd_str = replace_with_env_var(benchmark['command']).split(" ")
        orch_time, orch_output, orch_error = run_command_with_orch(orch_cmd_str, benchmark['orch_args'], working_dir)
        bash_times.append(bash_time)
        orch_times.append(orch_time)
        diff_lines = compare_results(bash_output, orch_output)
        diff_percentage = abs((bash_time - orch_time) / bash_time) * 100
        
        print_results(benchmark['name'], bash_time, orch_time, diff_lines, diff_percentage)
        
        activities = parse_logs_into_activities(log_data=orch_error)
        if not args.no_plots:
            plot_gantt(activities, REPORT_OUTPUT_DIR, f"{benchmark['name']}_gantt", simple=True)

        print_exec_time_for_cmds(orch_error, benchmark['name'])
        
        # Instead of always saving the logs, check the argument:
        if not args.no_logs:
            save_log_data(orch_error, REPORT_OUTPUT_DIR, f"{benchmark['name']}_log.log")


    
    # Plot the results
    benchmark_names = [benchmark['name'] for benchmark in benchmarks_config]
    
    print(f"Execution graphs can be found in {REPORT_OUTPUT_DIR}")

    if not args.no_plots:
        plot_benchmark_times_combined(benchmark_names, bash_times, orch_times, REPORT_OUTPUT_DIR, "benchmark_times_combined")
        plot_benchmark_times_individual(benchmark_names, bash_times, orch_times, REPORT_OUTPUT_DIR, "benchmark_times_individual")


if __name__ == "__main__":
    args = parse_args()
    main()
