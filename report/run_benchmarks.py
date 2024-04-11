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
    for env_var in ['ORCH_TOP', 'WORKING_DIR', 'TEST_SCRIPT_DIR', 'RESOURCE_DIR', 'REPORT_OUTPUT_DIR', 'PASH_TOP', 'PASH_SPEC_TOP', 'ORCH_COMMAND']:
        print(f"    {env_var + ':':17s} {os.environ.get(env_var)}")

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmarking system for shell script executor.")
    parser.add_argument('--no-plots', action='store_true', help="Do not generate and save plot visualizations.")
    parser.add_argument('--no-logs', action='store_true', help="Do not save log files of benchmark runs.")
    parser.add_argument('--csv-output', action='store_true', help="Generate and save results in CSV format.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose output.")
    parser.add_argument('--config-file', type=str, default=None, help="Path to the benchmark configuration file. Default is 'benchmark_config.json'.")
    parser.add_argument('--setup-script', type=str, default=None, help="Path to a setup script to run before running any other benchmark.")
    parser.add_argument('--subset', type=str, default=None, help="Name of a subset of benchmarks to run. Will instead download and store outputs in the dir with the specified name.")
    parser.add_argument('--no-setup', action='store_true', help="Do not run any setup script before running benchmarks. Assumes subset is also set.")
    return parser.parse_args()

# Sets the required environment variables for the benchmarking process.
def set_environment_variables(args):
    os.environ['ORCH_TOP'] = os.environ.get('ORCH_TOP', subprocess.check_output(['git', 'rev-parse', '--show-toplevel', '--show-superproject-working-tree']).decode('utf-8').strip())
    os.environ['WORKING_DIR'] = os.path.join(os.environ['ORCH_TOP'], 'report')
    os.environ['UTIL_DIR'] = os.path.join(os.environ['ORCH_TOP'], 'util')
    if args.subset:
        os.environ['TEST_SCRIPT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'benchmarks', args.subset)
        os.environ['RESOURCE_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'resources', args.subset)
        os.environ['REPORT_OUTPUT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'output', args.subset)
    else:
        os.environ['TEST_SCRIPT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'benchmarks')
        os.environ['RESOURCE_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'resources')
        os.environ['REPORT_OUTPUT_DIR'] = os.path.join(os.environ['WORKING_DIR'], 'output')
    os.environ['PASH_TOP'] = os.path.join(os.environ['ORCH_TOP'], 'deps', 'pash')
    os.environ['PASH_SPEC_TOP'] = os.path.join(os.environ['ORCH_TOP'])
    os.environ['ORCH_COMMAND'] = os.path.join(os.environ['PASH_SPEC_TOP'], 'pash-spec.sh')
    add_kaggle_to_path()

def add_kaggle_to_path():
    try:
        result = subprocess.run(['find', os.path.expanduser('~'), '-name', 'kaggle'], capture_output=True, text=True, check=True)
        find_output = result.stdout.strip().split('\n')

        # Find the most likely path (assuming it's in some 'bin' directory)
        kaggle_path = next((path for path in find_output if 'bin' in path), None)

        if kaggle_path:
            # Extract the directory from the full path
            kaggle_dir = os.path.dirname(kaggle_path)

            # Add the directory to the PATH
            os.environ['PATH'] += os.pathsep + kaggle_dir
            print(f"Added {kaggle_dir} to PATH")
        else:
            print("Kaggle executable not found")
    except subprocess.CalledProcessError as e:
        print("Error finding kaggle command:", e)



def main():
    
    args = parse_args()
    
    set_environment_variables(args)

    if args.config_file is not None:
        if args.verbose:
            print(f"Config File: {args.config_file}")
        config_file_path = os.path.join(os.environ['WORKING_DIR'], args.config_file)
    elif args.subset:
        config_file_path = os.path.join(os.environ['TEST_SCRIPT_DIR'], "setup", "config.json")
    else:
        config_file_path = os.path.join(os.environ['WORKING_DIR'], "benchmark_config.json")
        
    # Parse benchmark configurations
    config_parser = ConfigParser(os.path.join(os.environ['WORKING_DIR'], config_file_path))
    config_parser.parse_config()

    Path(os.environ['RESOURCE_DIR']).mkdir(parents=True, exist_ok=True)
    Path(os.environ['REPORT_OUTPUT_DIR']).mkdir(parents=True, exist_ok=True)
    
    if args.verbose:
        print_startup_info(args)
        print(config_parser)

    
    if args.setup_script:
        if args.verbose:
            print(f"Running setup script: {args.setup_script}")
        subprocess.run(['bash', args.setup_script])
    elif args.subset and not args.no_setup:
        setup_script = os.path.join(os.environ['TEST_SCRIPT_DIR'], "setup", 'setup.sh')
        if os.path.exists(setup_script):
            if args.verbose:
                print(f"Running setup script: {args.setup_script}")
            subprocess.run(['bash', setup_script])
        elif args.verbose:
                print(f"No setup script found in {os.environ['TEST_SCRIPT_DIR']}, ignoring")
    
    # Initialize and run the BenchmarkRunner
    runner = BenchmarkRunner(config_parser.get_benchmarks(), args)
    runner.run_all_benchmarks()

    # Generate reports if needed
    runner.generate_reports()

if __name__ == "__main__":
    main()
