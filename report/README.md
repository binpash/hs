# hs Benchmark Directory README

Welcome to the benchmark directory of the `hs`. This directory contains the essential tools and scripts to run benchmarks, analyze logs, and generate reports.

## Overview

The benchmarking tool provides an interface to run different benchmarks, collect performance metrics, and visualize the results through plots. It supports a wide range of features including:
- Running benchmarks with `bash` and `hs`.
- Comparing the outputs and performance of `Bash` and `hs`.
- Generating Gantt charts for each benchmark.
- Producing detailed logs and CSV results.

## Environment Variables

The benchmarking tool sets up and exports a few essential environment variables for the system:

- `WORKING_DIR`: The directory for the benchmarks and reports.
- `TEST_SCRIPT_DIR`: The directory containing benchmark scripts.
- `RESOURCE_DIR`: The directory to store resources required by benchmarks.
- `PASH_TOP`: The directory of `pash`.
- `PASH_SPEC_TOP`: The top directory of `hs`.

## Command-Line Interface

The primary command-line interface for the benchmark runner includes:
- `--no-plots`: Do not generate plots.
- `--no-logs`: Do not save log files.
- `--csv-output`: Save the results in CSV format.

## Benchmark Configuration

Benchmarks are configured using the `benchmark_config.json` file. Each benchmark in the configuration has the following properties:

- `name`: The name of the benchmark.
- `env`: A list of environment variables required by the benchmark. 
- `pre_execution_script`: A list of commands to run before executing the benchmark. Useful for fetching data or setting up the environment.
- `command`: The command or script to benchmark.
- `orch_args`: Arguments to pass to the `orch` system when running the benchmark.

Example:

```json
[
    {
        "name": "Dgsh 1.sh - 120M",
        "env": ["INPUT_FILE={RESOURCE_DIR}/in120M.xml"],
        "pre_execution_script": ["wget -nc -O in120M.xml http://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/dblp/dblp.xml"],
        "command": "{TEST_SCRIPT_DIR}/dgsh/1.sh",
        "orch_args": "-d 2 --sandbox-killing"
    }
]
```

## Running Benchmarks

To run benchmarks:

1. Navigate to the directory containing the benchmark runner (`cd ./report` from the top-level directory).
2. Execute the benchmark runner with desired arguments, e.g., `python3 benchmark_runner.py --csv-output`.

After running, the results, including logs, plots, and CSV files (if selected), will be saved in the `report_output` directory.

## Results Interpretation

The results include:
- Execution times for `bash` and `hs`.
- A comparison of the execution times.
- Validity checks for the outputs.
- Detailed execution logs.
- Gantt and bar charts visualizing the execution.

## Contributions

Feel free to contribute to the benchmark suite by adding new benchmarks or improving existing ones. Ensure that any new benchmarks have the necessary configuration in the `benchmark_config.json` file. 
