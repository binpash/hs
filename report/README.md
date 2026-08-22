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

## Branch note: strace baseline

This branch is the **strace baseline** for comparing against the fstrace
tracer on `better-benchmarks`. It carries the same benchmark harness (run_base
targets, output layout, manifests, hs log separation) but keeps `main`'s
tracer: `executor/template_script_to_execute.sh` runs the command under
`strace -y -f --seccomp-bpf --trace=fork,clone,%file` *inside* the sandbox, and
the scheduler reads the whole trace from the overlay upperdir once the command
finishes.

Because the trace file only becomes readable at completion, this branch also
keeps `main`'s batch dependency resolution -- the streaming read/write sets on
`better-benchmarks` are not separable from fstrace. A run-to-run comparison
therefore measures *fstrace + streaming* against *strace + batch*, not the
tracer alone.

The `fstrace` target is removed from every runner here, and the docker
invocation drops the eBPF mounts and raised memlock limit that only fstrace
needed.

## Output layout

Each run writes into `output/<suite>/<test>/`:

| Path | Contents |
|---|---|
| `<target>/` | the program's `OUTPUT_DIR` — **only** files the benchmark script wrote |
| `<target>_stdout`, `<target>_stderr` | what the script printed |
| `<target>_time` | wall-clock seconds |
| `<target>_hashes` | one digest per output file (see *Comparing outputs*) |
| `hs_log` | hs's own log: scheduler daemon, preprocessor, JIT runtime |
| `hs_internal_log` | stdout/stderr of hs's internal tooling (`try`, `strace`, tracebacks) |
| `strace_log` | strace trace of the `sh` run (the `strace` target) |
| `error` | empty when the `sh` and `hs` runs agree, otherwise why they do not |

The rule is one line: `<target>/` belongs to the program, `<target>_*` belongs to
the harness. Nothing the harness records is written inside `OUTPUT_DIR`, so
"every file in the output directory" is already exactly the benchmark's result
and needs no exclusion list.

## Comparing outputs

Two runs are compared on three things: their output files, their stdout, and
their stderr. `hs` keeps all of its own logging off the script's stdout and
stderr (see below), so a difference in either is a real difference in what the
script printed.

Output files are compared by digest. Each file named by the test's manifest is
hashed on its own into `<target>_hashes`, and those listings are compared, so a
failure names the file that diverged instead of just reporting a mismatch.

## Output manifests

A test may ship an `outputs` file naming the files that actually matter:

```
# Lines are glob patterns. '**' recurses. Blank lines and '#' are ignored.
*.out
results/**/*.txt

# A pattern may say how to read a file before hashing it, for formats whose
# bytes carry more than the payload -- a gzip member records the mtime of the
# data it compressed, so identical input still yields different bytes each run.
archive/*.gz => gzip
```

Patterns resolve against the run's output directory unless they are absolute
after environment-variable expansion, which is how a benchmark that writes
outside `OUTPUT_DIR` names its results. Normalizers are `raw` (the default),
`gzip`, `bzip2` and `xz`; `.gz`, `.bz2` and `.xz` pick theirs automatically.

Lookup order is `<test>/outputs`, then `<suite>/outputs` (shared by every test
in the suite), then the built-in default `**/*`. Most benchmarks need no
manifest at all — the default is already right. Write one when the benchmark
produces scratch files worth skipping (see `web-index/inner/outputs`), reports
only on stdout (`max_temp/inner/outputs`), or writes results elsewhere.

The implementation is `output_manifest.py`, which is also usable on its own.

## hs logging

`hs` writes four log streams, each separately redirectable, and none of them
touch the script's stdout or stderr:

| Flag | Stream |
|---|---|
| `--jit-log` | JIT runtime records (needs `-d 2` or higher) |
| `--scheduler-log` | scheduler daemon log |
| `--preprocessor-log` | preprocessor log |
| `--internal-log` | stdout/stderr of `try`, `strace`, Python tracebacks |
| `--combined-log` | all four at once |

All four default to stderr, so running `hs` by hand is unchanged. Point them at
files (or `/dev/null`) and the script's stdout and stderr carry nothing but the
script's own output — which is what makes them comparable against `sh`. Streams
pointed at the same file share a single descriptor rather than opening it
twice. The only thing `hs` still writes to stderr is a fatal error before the
script starts.

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

To execute benchmarks:

1. Navigate to the benchmark runner directory (e.g., `cd ./report`).
2. Run the benchmark runner with the desired arguments (e.g., `python3 main.py --csv-output`).

Results, including logs, plots, and CSV files, are saved in the `report_output` directory.

## Results Interpretation

Results encompass:

- Execution times for `bash` and `hs`.
- Comparative analysis of execution times.
- Validity checks of outputs.
- Execution logs and error messages in verbose mode.
- Gantt charts for timeline analysis and bar charts for speculative execution analysis.

## Contributions

Contributions to enhance or expand the benchmark suite are welcome. When adding new benchmarks, ensure to update `benchmark_config.json` accordingly.