## Koala Artifact for `hs`

### Overview

`hs` is a system for executing shell scripts out of order in a correct
manner. This document describe how to run the evaluation of `hs` on
different benchmarks in the paper.

### Security Warning

We assume password-less `sudo` is available to the running account. It is needed for privileged docker feature as well as using cgroup.

### System Requirement

The evaluation process (especially if running all benchmarks) uses
large amount of disk space for docker images (>700GB in total).  `hs`
also requires the `/tmp` directory is large enough to store intermediate
results (> 500GB).

### Running Benchmarks

First, make sure docker is installed.

Then, at the root directory of the project, run `docker build . -t hs`.

To run benchmarks, run `./report/run.sh`. It will take all the
benchmarks in `./report/koala_benchmarks` (which is a subset of
`./report/all_benchmarks`) and run them. This subset is not
particularly disk consumption heavy (~90GB).

`./report/run.sh` first runs the setup for each benchmark set, then
runs each individual benchmark. The results will be output into
`dynamic-parallelizer/report/output/`.

The `HSTMP` variable inside `./report/run.sh` can be set to use a
different location for intermediate result storage. 

Everything in `hs`'s README originally is below. But they are not
required to run the evaluation.

## Original `hs` README
The project's top-level directory contains the following:

- `deps`: Dependencies required by `hs`.
- `docs`: Documentation and architectural diagrams.
- `model-checking`: Tools and utilities for model checking.
- `parallel-orch`: Main orchestration components.
- `pash-spec.sh`: Entry script to initiate the `hs` process.
- `README.md`: This documentation file.
- `report`: Generated reports related to test runs and performance metrics.
- `requirements.txt`: List of Python dependencies.
- `Rikerfile`: Configuration file for Riker.

### Installation

Install `hs` on your Linux-based machine by following these steps:

**Note:** Currently works with `Ubuntu 20.04` or later

1. Navigate to the project directory:
   ```sh
   cd path_to/dynamic-parallelizer
   ```

2. Run the installation script:
   ```sh
   ./scripts/install_deps_ubuntu20.sh
   ```

This script will handle all the necessary installations, including dependencies, try, Riker, and PaSh.

### Running `hs`

The main entry script to initiate `hs` is `pash-spec.sh`. This script sets up the necessary environment and invokes the orchestrator in `parallel-orch/orch.py`. It's designed to accept a variety of arguments to customize its behavior, such as setting debug levels or specifying log files.

Example of running the script:

```bash
./pash-spec.sh [arguments] script_to_speculatively_run.sh
```

**Arguments**:

- `-d, --debug-level`: Set the debugging level. Default is `0`.
- `-f, --log_file`: Define the logging output file. By default, logs are printed to stdout.
- `--sandbox-killing`: Kill any running overlay instances before committing to the lower layer.
- `--env-check-all-nodes-on-wait`: On a wait, check for environment changes between the current node and all other waiting nodes. (not fully functional yet!)

### Testing

To run the provided tests:

```bash
./test/test_orch.sh
```

For in-depth analysis, set the `DEBUG` environment variable to `2` for detailed logs and redirect logs to a file:

```bash
DEBUG=2 ./test/test_orch.sh 2>logs.txt
```

### Contributing and Further Development

Contributions are always welcome! The project roadmap includes extending the architecture to support complete scripts, optimizing the scheduler for better performance, etc.

For a detailed description of possible optimizations, see the [related issues](https://github.com/binpash/dynamic-parallelizer/issues?q=is%3Aopen+is%3Aissue+label%3Aoptimization)

### License

`hs` is licensed under the MIT License. See the `LICENSE` file for more information.
