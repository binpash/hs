import argparse
import os
import subprocess
from config_parser import ConfigParser
from benchmark_runner import BenchmarkRunner
from pathlib import Path


def print_startup_info(args):
    print("Startup Information:")
    print("> Command-line Arguments:")
    for arg, value in vars(args).items():
        print(f"    {arg + ':':13s} {value}")

    print("> Environment Variables:")
    for env_var in ['ORCH_TOP', 'WORKING_DIR', 'TEST_SCRIPT_DIR', 'RESOURCE_DIR', 'PASH_TOP', 'PASH_SPEC_TOP']:
        print(f"    {env_var + ':':17s} {os.environ.get(env_var)}")

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmarking system for shell script executor.")
    parser.add_argument('--no-plots', action='store_true', help="Do not generate and save plot visualizations.")
    parser.add_argument('--no-logs', action='store_true', help="Do not save log files of benchmark runs.")
    parser.add_argument('--csv-output', action='store_true', help="Generate and save results in CSV format.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output.")
    parser.add_argument('--full-gantt', action='store_false', help="Generate a full Gantt chart for each benchmark.")
    
    return parser.parse_args()


# Sets the required environment variables for the benchmarking process.
def set_environment_variables():
    os.environ['ORCH_TOP'] = os.environ.get('ORCH_TOP', subprocess.check_output(['git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']).decode('utf-8').strip())
    os.environ['WORKING_DIR'] = os.path.join(os.environ['ORCH_TOP'], 'report')
    os.environ['TEST_SCRIPT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'benchmarks')
    os.environ['RESOURCE_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'resources')
    os.environ['PASH_TOP'] = os.path.join(os.environ['ORCH_TOP'], 'deps', 'pash')
    os.environ['PASH_SPEC_TOP'] = os.path.join(os.environ['ORCH_TOP'])
    os.environ['ORCH_COMMAND'] = os.path.join(os.environ['PASH_SPEC_TOP'], 'pash-spec.sh')
    os.environ['REPORT_OUTPUT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'output')

def main():
    
    set_environment_variables()
    args = parse_args()
    
    # Parse benchmark configurations
    config_parser = ConfigParser(os.path.join(os.environ['WORKING_DIR'], 'benchmark_config.json'))
    config_parser.parse_config()
    
    Path(os.environ['RESOURCE_DIR']).mkdir(parents=True, exist_ok=True)
    Path(os.environ['REPORT_OUTPUT_DIR']).mkdir(parents=True, exist_ok=True)
    
    if args.verbose:
        print_startup_info(args)
    
    # Initialize and run the BenchmarkRunner
    runner = BenchmarkRunner(config_parser.get_benchmarks(), args)
    runner.run_all_benchmarks()

    # Generate reports if needed
    runner.generate_reports()

if __name__ == "__main__":
    main()
