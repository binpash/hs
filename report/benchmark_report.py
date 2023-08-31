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

def resolve_working_dir(path):
    return path.format(RESOURCE_DIR=os.environ.get('RESOURCE_DIR'))

def resolve_command_path(command):
    return command.format(TEST_SCRIPT_DIR=os.environ.get('TEST_SCRIPT_DIR'))


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
    print(f"Bash Execution Time:    {bash_time}s")
    print(f"hs Execution Time:      {orch_time}s")
    print(f"Valid:                  {'Yes' if len(diff_lines) == 0 else 'No - see below'}")
    for line in diff_lines:
        print(line)
    print(comparison_result)
    
    print("-" * 40)
    print("-" * 40)


def main():
    # Load benchmark configurations
    with open(os.path.join(os.environ.get('WORKING_DIR'), 'benchmark_config.json'), 'r') as f:
        benchmarks_config = json.load(f)
        
    bash_times = []
    orch_times = []

    for benchmark in benchmarks_config:
        # Create resource dir if non-existent
        os.makedirs(os.environ.get('RESOURCE_DIR'), exist_ok=True)
        # Run pre-execution commands
        for pre_command in benchmark.get('pre_execution_script', []):
            logging.debug(f"|Pre-execution: {pre_command}")
            run_pre_execution_command(pre_command, os.environ.get('RESOURCE_DIR'))

        # TODO: in the future, we are going to parse the orch_error and generate reports
        working_dir = resolve_working_dir(benchmark.get('working_dir', os.environ.get('TEST_SCRIPT_DIR')))
        
        bash_time, bash_output, _bash_error = run_command([BASH_COMMAND, resolve_command_path(benchmark['command'])], working_dir)
        orch_time, orch_output, orch_error = run_command([ORCH_COMMAND, benchmark['orch_args'], resolve_command_path(benchmark['command'])], working_dir)
        bash_times.append(bash_time)
        orch_times.append(orch_time)
        # print(bash_output)
        diff_lines = compare_results(bash_output, orch_output)
        diff_percentage = abs((bash_time - orch_time) / bash_time) * 100
        print_results(benchmark['name'], bash_time, orch_time, diff_lines, diff_percentage)

    # Create output dir for reports
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    # Plot the results
    benchmark_names = [benchmark['name'] for benchmark in benchmarks_config]
    plot_benchmark_times_combined(benchmark_names, bash_times, orch_times, REPORT_OUTPUT_DIR, "benchmark_times_combined")
    plot_benchmark_times_individual(benchmark_names, bash_times, orch_times, REPORT_OUTPUT_DIR, "benchmark_times_individual")
    print(f"Execution graphs can be found in {REPORT_OUTPUT_DIR}")

if __name__ == "__main__":
    main()
