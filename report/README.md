# hs Benchmark Directory README

This is the benchmark directory of `hs`. This directory contains essential tools and scripts for running benchmarks, analyzing logs, generating reports, and visualizing results.

## Overview

The benchmarking tool offers a comprehensive interface to evaluate the performance of `hs` against `bash`, supporting a range of features:

- Execution of benchmarks using both `bash` and `hs`.
- Comparison of outputs and performance metrics between `Bash` and `hs`.
- Generation of detailed reports including Gantt charts for in-depth analysis.
- Creation of CSV files for data analysis and bar charts for visual comparison.
- Optional verbose output for detailed execution logs.

## Environment Variables

Several environment variables are essential for the benchmarking tool's operation:

- `ORCH_TOP`: The top directory of the orchestrator system.
- `WORKING_DIR`: Directory for benchmarks and reports.
- `TEST_SCRIPT_DIR`: Directory containing benchmark scripts.
- `RESOURCE_DIR`: Directory for storing resources required by benchmarks.
- `PASH_TOP`: The directory of `pash`.
- `PASH_SPEC_TOP`: The top directory of `hs`.

## Command-Line Interface

The benchmark runner's command-line interface includes options for controlling the output and behavior:

- `--no-plots`: Disables the generation of plot visualizations.
- `--no-logs`: Prevents saving log files.
- `--csv-output`: Enables saving results in CSV format.
- `--verbose`: Enables verbose output, providing detailed logs of the benchmarking process.
- `--full-gantt`: Generate a full Gantt chart for each benchmark.

## Benchmark Configuration

Benchmarks are configured via `benchmark_config.json`, with each entry specifying:

- `name`: Benchmark name.
- `env`: Environment variables required by the benchmark.
- `pre_execution_script`: Commands for initial setup, like fetching data.
- `command`: The benchmark command or script.
- `orch_args`: Arguments for the `hs` system.

Example configuration:

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

The paper uses presentation names for benchmarks, while this directory preserves
several original workload names. The main mapping is:

| Paper reference | Benchmark directory | Notes |
| --- | --- | --- |
| TERA-Seq | `report/benchmarks/teraseq` | Dataset-specific runs live under `teraseq/<dataset>/`. |
| Genomics | `report/benchmarks/bio4` | Original Bio4 workflow directory. |
| Sklearn | `report/benchmarks/sklearn_large` | Paper-scale run; `sklearn` is a smaller sanity benchmark. |
| DGSH | `report/benchmarks/dgsh` | Individual scripts are subdirectories. |
| NLP | `report/benchmarks/nlp` | Variants include `nlp10x`, `nlp100x`, `nlp1000x`, `nlp1m`, `nlp10m`, and `nlp100m`. |
| NOAA | `report/benchmarks/max_temp` | NOAA max-temperature workload. |
| Unix50 | `report/benchmarks/unix_50` | Full and inflated inputs are under `unix_50/full*`. |
| COVID-mts | `report/benchmarks/bus-analytics` | Original transit/bus analytics workload. |
| LogAnalysis | `report/benchmarks/log-analysis` | Size variants are `small`, `medium`, and `full`. |
| WebIndex | `report/benchmarks/web-index` | Web-index input variants are under `web-index/web-index*`. |
| Microbenchmarks | `report/benchmarks/micro`, `report/benchmarks/micro_try` | Overhead and synthetic stress benchmarks. |

For Docker-backed benchmarks, use the historical benchmark pipeline:

1. From the repository root, build the base image: `docker build -t hs .`
2. Run `./report/benchmarks/<bench>/setup`.
3. Run `./report/benchmarks/<bench>/<optional-subbenchmark>/run`.

For example:

```sh
docker build -t hs .
# Small Sklearn sanity benchmark; the paper-scale Sklearn row is sklearn_large.
./report/benchmarks/sklearn/setup
./report/benchmarks/sklearn/run --target both --window 16
```

If your Docker daemon requires root privileges, run the first command with
`sudo`; the benchmark setup/run wrappers will use `sudo docker` internally when
plain `docker` cannot access the daemon.

The common run flags are:

- `--target both`: run `/bin/sh`, run hS, and compare outputs.
- `--target sh-only`: run only the shell baseline.
- `--target hs-only`: run only hS.
- `--window N`: set the hS speculation window size.
- `--log enable|disable`: include or suppress hS debug logging.

Results, including logs and timing files, are saved under `report/output/`.
Each Docker wrapper prints the output directory at the end and refreshes
`report/output/results_summary.csv`. Regenerate the CSV manually with:

```sh
python3 report/summarize_results.py
```

To run the full list in `report/all_benchmarks`:

```sh
docker build -t hs .
./report/setup_all_benchmarks.sh
./report/run_all_benchmarks.sh --target both --window 16 --log disable
```

This can take many hours to days and hundreds of GB. TERA-Seq setup alone takes
about 6 hours and roughly 500 GB of local storage. Docker is convenient for
reproducibility, but may slow sandboxing-heavy paths by about 10-20% compared
with native CloudLab-style runs.

## Results Interpretation

Results encompass:

- Execution times for `bash` and `hs`.
- Comparative analysis of execution times.
- Validity checks of outputs.
- Execution logs and error messages in verbose mode.
- Gantt charts for timeline analysis and bar charts for speculative execution analysis.

## Contributions

Contributions to enhance or expand the benchmark suite are welcome. When adding new benchmarks, ensure to update `benchmark_config.json` accordingly.
