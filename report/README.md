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

## Running a benchmark: two commands

```
cd report/benchmarks/<suite>
./setup                              # 1. build hs/<suite>; 2. download inputs to report/resources/<suite>/
./<size>/run --target sh hs          # run (./run for single-level suites such as sklearn)
```

Add `--local` to either command to skip docker and use this machine directly.
Both are symlinks to `report/setup_base` and `report/run_base`; every suite
behaves the same way (teraseq and the archived suites are bespoke and are not
covered).

**Images hold tools, never data.** `hs/<suite>` is the base `hs` image plus
that suite's runtime tools (samtools, pandoc, FFmpeg's libraries, ...) and its
scripts. Inputs are downloaded once onto the host, into
`report/resources/<suite>/`, and bind-mounted **read-only** into the container
at run time. So rebuilding `hs` never re-downloads anything, and the same
inputs serve every hs checkout on the machine. `./setup` runs the suite's
`inner/setup` inside `hs/<suite>` with `resources/` mounted read-write, so the
host needs nothing but docker; extra arguments go to `inner/setup` (bio4:
`./setup -i small/list` for the 700 MB small set instead of all 100 GB).

Inside the container, `report/resources` is a per-run copy-on-write overlay
over that read-only mount, set up by `entrypoint.sh` through an idmapped bind
(util-linux >= 2.39, present in the image) that presents the host owner as
root, since hs's sandbox runs in a user namespace mapping only root and could
not otherwise write the files. A benchmark that writes
into its own input directory -- max_temp regenerates `$RESOURCE_DIR/<year>.txt`
every run -- therefore works in docker mode, and its writes vanish with the
container. In `--local` mode there is no overlay: such writes land in the host
directory.

**Where things live.** Inputs, the container's `/tmp` (hs scratch, try's
mount logs, that overlay upper) and, on a prepared machine, docker's images
and container layers all sit under one *data directory* on the big disk,
found by `report/hs_data_dir`: `$HS_DATA`, else `~/.config/hs/data_dir`, else
`/mydata/hs` if `/mydata` exists, else `report/` itself. On a fresh node run

```sh
scripts/setup_benchmark_machine.sh      # once per machine: docker, disk choice, data dir
```

which installs docker, picks the disk (largest SSD with room, else largest
anything; a blank extra drive gets formatted after confirmation; `--disk`
overrides), creates `<disk>/hs/{resources,tmp,docker}`, points docker's
data-root there, and moves any inputs already in `report/resources` across,
leaving a symlink. CloudLab's root partition is ~16 GB, so without this step
images alone fill it.

Each run gets its own subdirectory of that `tmp/`, removed when the container
exits. `run --keep` leaves it in place and prints the path; it then holds
`pash_spec/` (hs's per-command scripts, env snapshots, traces, captured
outputs, and on this branch try's sandboxes too), and
`hs-inputs-cow/` (what the benchmark wrote into its inputs). Outputs and logs
are always copied to `report/output/<test>` regardless.

On a small machine, pass `--window 4` or so; the default of 16 assumes a
many-core benchmark host.

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
`gzip`, `bzip2`, `xz` and `bam`; `.gz`, `.bz2`, `.xz` and `.bam` pick theirs
automatically. `bam` hashes a BAM as SAM text minus its `@PG` lines, because
samtools records its full command line -- output path included -- in one; it
needs `samtools` on `PATH`, which any image producing BAMs has.

Two accommodations let a script be benchmarked *unmodified* even though the
harness gives each target its own output directory:

- A `--env_vars` value may contain `$OUTPUT_DIR`; it is expanded per target.
  bio4's `fxbio4.sh` reads `OUT`, so its runner passes `'OUT=$OUTPUT_DIR'`.
- stdout and stderr are compared with each target's own output directory
  masked, so a script that prints where it wrote is not reported as differing.

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