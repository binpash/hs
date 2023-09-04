import subprocess
import time
import json
import os
from benchmark_plots import *
import logging
import difflib

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

def replace_with_env_var(input_string):
    format_args = {
        "TEST_SCRIPT_DIR": os.environ.get("TEST_SCRIPT_DIR", os.getcwd()),
        "RESOURCE_DIR": os.environ.get("RESOURCE_DIR", os.getcwd())
    }
    replaced_string = input_string.format(**format_args)
    return replaced_string

def run_pre_execution_command(command, working_dir=os.getcwd()):
    print("Running pre-execution command:", command)
    process = subprocess.Popen(command.strip().split(" "), cwd=working_dir)
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
    for line in diff_lines:
        print(line)
    print(comparison_result)
    print("-" * 40)
    print()
    
def print_sorted_logs(orch_output):
    relevant_lines = [line for line in orch_output.split("\n") if line.startswith("INFO:root:>|")]
    # Extract lines with step time and sort
    step_time_lines = [(line, float(line.split("Step time:")[1].split("ms")[0])) for line in relevant_lines if "Step time:" in line]
    sorted_step_time_lines = sorted(step_time_lines, key=lambda x: x[1], reverse=True)

    for entry in sorted_step_time_lines:
        split_line = entry[0].split("|")[1:]
        pretty_line = " | ".join(split_line)
        print(f"{pretty_line}, Step Time: {entry[1]:.3f}ms")
        

def print_exec_time_for_cmds(orch_outpt):
    # Split the log into lines and filter the relevant ones
    relevant_lines = [line.replace("INFO:root:>|PartialOrder|RunNode,", "") for line in orch_outpt.split("\n") if line.startswith("INFO:root:>|PartialOrder|RunNode,") and "Step time:" in line]
    # Extract lines with RunNode commands and their step times
    node_and_times = [(int(line.split("|")[0]), float(line.split("|")[1].split(":")[1][:-2]), float(line.split("|")[2].split(":")[1][:-2])) for line in relevant_lines]

    # Total number of times a RunNode command was executed
    total_run_node_commands = len(node_and_times)
    # print(node_and_times)
    # Total time of all RunNode commands
    total_time = sum([entry[2] for entry in node_and_times])
    
    # Extract and sum the total time of the step per node
    node_times = {}
    counts = {}
    for node, _, time in node_and_times:
        if node in node_times:
            node_times[node] += time
            counts[node] += 1
        else:
            node_times[node] = time
            counts[node] = 1

    print("-" * 40)
    print(f"Total number of times a RunNode command was executed: {total_run_node_commands}")
    print(f"Total time of all RunNode commands: {total_time:.3f}ms")
    print("\nTotal time of the step per node:")
    for node, time in sorted(node_times.items(), key=lambda x: x[1], reverse=True):
        print(f"{node}: {time:.3f}ms ({counts[node]} times)")
    print("-" * 40)


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

    for benchmark in benchmarks_config:
        
        # Set up preferred environment
        export_env_vars(benchmark.get('env', {}))
        # Create resource dir if non-existent
        os.makedirs(os.environ.get('RESOURCE_DIR'), exist_ok=True)
        # Run pre-execution commands
        for pre_command in benchmark.get('pre_execution_script', []):
            logging.debug(f"|Pre-execution: {pre_command}")
            run_pre_execution_command(pre_command, os.environ.get('RESOURCE_DIR'))

        # TODO: in the future, we are going to parse the orch_error and generate reports
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
        
    print_exec_time_for_cmds(orch_error)

    # Create output dir for reports
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    # Plot the results
    benchmark_names = [benchmark['name'] for benchmark in benchmarks_config]
    # print_sorted_logs(orch_error)
    plot_benchmark_times_combined(benchmark_names, bash_times, orch_times, REPORT_OUTPUT_DIR, "benchmark_times_combined")
    plot_benchmark_times_individual(benchmark_names, bash_times, orch_times, REPORT_OUTPUT_DIR, "benchmark_times_individual")
    print(f"Execution graphs can be found in {REPORT_OUTPUT_DIR}")
    

if __name__ == "__main__":
    main()
