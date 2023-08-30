import subprocess
import time
import json
import os
import matplotlib.pyplot as plt
from benchmark_plots import *

# Setting and exporting environment variables (same as tests for now).
# This will change in the future.
os.environ['ORCH_TOP'] = os.environ.get('ORCH_TOP', subprocess.check_output(['git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']).decode('utf-8').strip())
os.environ['WORKING_DIR'] = os.path.join(os.environ['ORCH_TOP'], 'test')
os.environ['TEST_SCRIPT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'test_scripts')
os.environ['MISC_SCRIPT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'misc')

BASH_COMMAND = "/bin/bash"
ORCH_COMMAND = os.path.join(os.environ['ORCH_TOP'], 'pash-spec.sh')

def run_command(command):
    print("Running command: ", command)
    start_time = time.time()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    end_time = time.time()
    return (end_time - start_time, stdout.decode('utf-8'), stderr.decode('utf-8'))

# TODO: Make this more robust - maybe even use sth like difflib
def compare_results(bash_output, orch_output):
    return bash_output == orch_output

def main():
    # Load benchmark configurations
    with open('benchmark_config.json', 'r') as f:
        benchmarks_config = json.load(f)
        
    bash_times = []
    orch_times = []

    for benchmark in benchmarks_config:
        # Run pre-execution commands
        for pre_command in benchmark.get('pre_execution_script', []):
            run_command(pre_command)

        # TODO: in the future, we are going to parse the orch_error and generate reports
        bash_time, bash_output, _bash_error = run_command([BASH_COMMAND, os.environ.get('TEST_SCRIPT_DIR') + "/" + benchmark['bash_command']])
        orch_time, orch_output, orch_error = run_command([ORCH_COMMAND, benchmark['orch_args'], os.environ.get('TEST_SCRIPT_DIR') + "/" + benchmark['bash_command']])
        bash_times.append(bash_time)
        orch_times.append(orch_time)
        are_results_same = compare_results(bash_output, orch_output)

        print(f"Results for benchmark: {benchmark['name']}")
        print(f"Bash Execution Time: {bash_time}s")
        print(f"orch Execution Time: {orch_time}s")
        print(f"Are outputs the same? {'Yes' if are_results_same else 'No'}")
        print("-------------------------------")

    # Plot the results
    benchmark_names = [benchmark['name'] for benchmark in benchmarks_config]
    plot_benchmark_results(benchmark_names, bash_times, orch_times)


if __name__ == "__main__":
    main()
