import csv
from typing import List
from command_executor import CommandExecutor
from config_parser import BenchmarkConfig
from result_analyzer import ResultAnalyzer
from report_generator import ReportGenerator
import benchmark_plots
import os
from pprint import pprint

class BenchmarkRunner:
    def __init__(self, benchmarks: "List[BenchmarkConfig]", args):
        self.benchmarks = benchmarks
        self.args = args
        self.results = []
        self.activities = {}
        
    def __repr__(self):
        return (f"BenchmarkRunner(benchmarks={self.benchmarks!r}, "
                f"args={self.args!r}, results={self.results!r})")
        
    def __str__(self):
        return (f"Benchmark Runner:\n"
                f"  Benchmarks: {self.benchmarks}\n"
                f"  Arguments: {self.args}\n"
                f"  Results: {self.results}")


    def run_all_benchmarks(self):
        for benchmark in self.benchmarks:
            self.run_benchmark(benchmark)

    def run_benchmark(self, benchmark: BenchmarkConfig):
        # Setup environment and pre-execution commands
        benchmark.setup_environment()

        if self.args.verbose:
            # Print verbose information
            print(f"\n---------> Running benchmark: {benchmark.name} <---------\n")
            print(">", benchmark)
        
        for pre_command in benchmark.pre_execution_script:
            CommandExecutor.run_pre_execution_command(pre_command, os.environ.get('RESOURCE_DIR'), self.args.verbose)

        # Execute the benchmark
        bash_time, bash_output, _ = CommandExecutor.run_command(
            benchmark.command.split(" "), 
            os.environ.get('TEST_SCRIPT_DIR'), 
            self.args.verbose)
        orch_time, orch_output, orch_log = CommandExecutor.run_command_with_orch(
            benchmark.command.split(" "), 
            benchmark.orch_args, 
            os.environ.get('TEST_SCRIPT_DIR'), 
            os.environ.get('ORCH_COMMAND'),
            self.args.verbose)
        
        prog_blocks = ResultAnalyzer.process_results(orch_log)
        # pprint(prog_blocks)

        # Analyze and compare results
        diff_lines = ResultAnalyzer.compare_results(bash_output, orch_output)
        self.results.append((benchmark.name, bash_time, orch_time, 'Yes' if len(diff_lines) == 0 else 'No', diff_lines))

        # Print results and optionally save logs
        ReportGenerator.print_results(benchmark.name, bash_time, orch_time, diff_lines, verbose=self.args.verbose)
        if not self.args.no_logs:
            ReportGenerator.save_log_data(orch_log, os.environ.get('REPORT_OUTPUT_DIR'), f"{benchmark.name}_log.log")
            
        self.activities[benchmark.name] = prog_blocks


    def generate_reports(self):
            # Generate CSV report if required
            if self.args.csv_output:
                ReportGenerator.generate_csv_report(self.results, os.environ.get('REPORT_OUTPUT_DIR'), "benchmark_results.csv")

            # Generate plots if required
            if not self.args.no_plots:
                self.generate_plots()

    def generate_plots(self):
        benchmark_names = [benchmark.name for benchmark in self.benchmarks]
        bash_times = [result[1] for result in self.results]
        orch_times = [result[2] for result in self.results]

        # Plot execution time comparisons
        benchmark_plots.plot_benchmark_times_combined(benchmark_names, bash_times, orch_times, os.environ.get('REPORT_OUTPUT_DIR'), "benchmark_times_combined")
        benchmark_plots.plot_benchmark_times_individual(benchmark_names, bash_times, orch_times, os.environ.get('REPORT_OUTPUT_DIR'), "benchmark_times_individual")

        # Plot Gantt charts for each benchmark
        for benchmark in self.benchmarks:
            activities = self.activities.get(benchmark.name)
            if activities:
                print(os.environ.get('REPORT_OUTPUT_DIR'), f"{benchmark.name}_gantt")
                benchmark_plots.plot_prog_blocks(activities, os.environ.get('REPORT_OUTPUT_DIR'), f"{benchmark.name}_gantt")
