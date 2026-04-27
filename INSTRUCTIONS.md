# Overview

This artifact accompanies the paper "hS: Speculative Script Reordering at
Subprocess Granularity."

**Note:** Due to the double-blind review process, the submitted paper version refers to the system as "Sys"; the published version will use the artifact and repository name, "hS."

OSDI '26 evaluates only the **Artifacts Available** badge. This file contains instructions for "available, functional, reproducible" steps so reviewers can quickly inspect availability and also see how to exercise the artifact and reproduce paper results. For the [**Artifact available**](#artifact-available-10-minutes) evaluation, please disregard the sections that follow.

The stable OSDI submission URL should be the Zenodo record for the archived release:

```text
Zenodo archive: https://doi.org/10.5281/zenodo.19832407
GitHub AE branch: https://github.com/binpash/hs/tree/osdi26-ae
Main repository: https://github.com/binpash/hs
```

The paper makes the following artifact-relevant claims:

1. **Speculative shell execution without annotations**: hS executes shell scripts
   speculatively and out of order at subprocess granularity, while preserving
   the original sequential behavior when speculation is safe.
2. **A concrete hS implementation**: the artifact includes the `hs` frontend,
   scheduler/orchestrator, executor, preprocessor, runtime support, tracing and
   sandboxing helpers, model-checking artifacts, and the `deps/try` substrate
   used to isolate and commit speculative effects.
3. **Performance, overhead, and frontend evaluation**: the artifact includes the
   benchmark suite, dataset manifest, plotting scripts, and precomputed results
   supporting the paper's overall performance, mis-speculation, executor
   overhead, varying-window, and Python-frontend results.

This artifact is organized around the following review activities:

* [Artifact available](#artifact-available-10-minutes): Reviewers can confirm
  that the paper, code, automation scripts, precomputed results, and dataset
  manifest are publicly available.
* [Artifact functional](#artifact-functional-20-minutes): Reviewers can install dependencies, inspect the key components, and run the smoke/correctness suite.
* [Results reproducible](#results-reproducible-20+hours): Reviewers can follow the roadmap to recreate the full results supporting the paper's claims on suitable hardware and regenerate representative plots.

# Artifact Available (10 minutes)

Confirm that the paper, code, and automation scripts are all available to
reviewers and, for the artifact materials, permanently public:

1. The artifact code is hosted on [GitHub; `osdi26-ae` branch](https://github.com/binpash/hs/tree/osdi26-ae).
2. The artifact is hosted in Zenodo's permanent archive:

   ```text
   https://doi.org/10.5281/zenodo.19832407
   ```

The accepted paper PDF is submitted separately through HotCRP and is not bundled
inside this artifact archive. The final paper will be available through the OSDI
proceedings.

The Zenodo archive should contain, and the GitHub branch should make available:

* This `INSTRUCTIONS.md` file.
* The source tree, including `hs`, `scheduler/`, `executor/`, `preprocessor/`,
  `jit_runtime/`, `model-checking/`, `test/`, `report/`, and `python_hs/`.
* The `deps/try` submodule contents. If using GitHub instead of the Zenodo
  archive, initialize it with:

  ```sh
  git submodule update --init --recursive deps/try
  ```

* Automation and helper scripts, including `scripts/install_deps_ubuntu20.sh`
  and `scripts/make_ae_archive.sh`.
* Precomputed results and plotting materials under `artifact/paper-results/`.
* Dataset locations under `artifact/datasets.md`.

# Artifact Functional (20 minutes)

Confirm sufficient documentation, key components as described in the paper, and
execution across hS's smoke/correctness suite:

* **Documentation**: The top-level [README](README.md), this file,
  [artifact/README.md](artifact/README.md),
  [artifact/datasets.md](artifact/datasets.md),
  [artifact/paper-results/README.md](artifact/paper-results/README.md),
  [report/README.md](report/README.md), and
  [python_hs/report/README.md](python_hs/report/README.md) describe the
  artifact, data, benchmark, and plotting layout.
* **Key components**: `hs`, `scheduler/`, `executor/`, `preprocessor/`,
  `jit_runtime/`, `model-checking/`, `deps/try`, `test/`,
  `report/benchmarks/`, and `python_hs/`.
* **Exercisability**: The instructions below install dependencies, build helper
  binaries, run a small hS command, and run the shell smoke/correctness suite.

**Quickstart (Ubuntu native):** These steps set up the artifact on an
Ubuntu-like Linux host and run the hS test suite.

Requirements:

1. Linux host, preferably Ubuntu 20.04 or newer.
2. Permission to install apt packages.
3. Python 3.12 or newer. The parser package used by hS contains Python 3.12
   syntax. Ubuntu 24.04 provides Python 3.12 by default. On Ubuntu 20.04/22.04,
   the setup script attempts to install Python 3.12 and `python3.12-venv` from
   the deadsnakes PPA when the default apt repositories do not provide them.
4. `sudo`/root permission to use the Linux tracing, cgroup, OverlayFS, and
   filesystem facilities needed by hS/`try`. A disposable VM or test host is
   recommended.

Download the repository with the required submodule:

```sh
git clone https://github.com/binpash/hs
cd hs
git switch osdi26-ae
./scripts/install_deps_ubuntu20.sh
```

Run the setup script as the regular checkout owner. It uses `sudo` internally
for apt packages and installing helper binaries.

If you start from the Zenodo archive instead of GitHub, unpack the archive,
enter the unpacked directory, and run:

```sh
./scripts/install_deps_ubuntu20.sh
```

The installer will:

1. Install system packages.
2. Initialize `deps/try`.
3. Build and install `try-commit` and `try-summary`.
4. Build `executor/fd_util` and `executor/set-diff`.
5. Create `python_pkgs/` and install the Python packages from
   `requirements.txt`.

After setup, run:

```sh
./hs --help
sudo ./hs -c 'echo hello'
```

The second command should print:

```text
hello
```

Run the tests to verify hS maintains correctness while speculatively running commands:

```sh
sudo env ORCH_TOP="$(pwd)" PASH_SPEC_TOP="$(pwd)" PASH_TOP="$(pwd)" ./test/test_orch.sh
```

The expected final line is:

```text
Summary: 40/40 tests passed.
```

**Complete exploration:** The main source directories are:

* `hs`: shell-script speculative execution entry point. `pash-spec.sh` is kept
  as a compatibility wrapper for older benchmark runners.
* `scheduler/`: command-state tracking and speculation/commit decisions.
* `executor/`: tracing, sandboxing, and helper binaries.
* `preprocessor/`: shell-to-runtime transformation.
* `jit_runtime/`: runtime support used by transformed scripts.
* `model-checking/`: Alloy models for scheduler/orchestrator behavior.
* `report/benchmarks/`: shell benchmark definitions and setup/run scripts.
* `python_hs/`: Python frontend prototype and Python benchmark materials.

# Results Reproducible (20+ hours)

The key results of hS's evaluation are the following:

* Overall hS and PaSh performance relative to Bash across the main shell
  benchmark suite.
* Mis-speculation and execution statistics.
* Executor overhead measurements, including tracing/sandboxing overheads and
  I/O-heavy/open-heavy stress tests.
* Performance trends under varying speculation-window sizes.
* Python frontend performance relative to standard Python execution.

**Preparation:** These steps assume the functional quickstart above has
completed successfully. For results reproduction, we recommend running on a
Docker-enabled Linux host. Full benchmark reruns require CloudLab-like Linux
machines, many cores, large local storage, privileged Docker containers,
filesystem/cgroup support, and several hours. The paper used CloudLab `r6525`
machines with two 32-core AMD EPYC 7543 CPUs, 256 GB RAM, NVMe storage, Docker
27.3.1, Bash 5.1.16, and Python 3.12+ for this released artifact.

Install Docker on Ubuntu:

```sh
# Add Docker's official GPG key.
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources.
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo docker run hello-world
```

The benchmark scripts call `docker` directly when the current user can access
the Docker daemon. If `docker build` reports a socket-permission error, either
prefix Docker commands with `sudo` or add the user to the Docker group and log
in again:

```sh
sudo usermod -aG docker "$USER"
```

Build the hS artifact image. The benchmark Dockerfiles use `FROM hs`, so this
base image must exist before running benchmark setup scripts:

```sh
docker build -t hs .
docker run --rm --privileged --cgroupns=host hs ./hs -c 'echo hello'
```

The container command should print `hello` and exit successfully. If your
Docker daemon requires root privileges, prefix these two commands with `sudo`.

Large public datasets are not bundled in the archive. Permanent locations,
access notes, and benchmark mappings are listed in
[`artifact/datasets.md`](artifact/datasets.md).

AEC reviewers may inspect the precomputed results in
[`artifact/paper-results`](artifact/paper-results) and regenerate the paper
plots without launching the full experiments.

**Regenerate plots from precomputed results:** From the repository root, run:

```sh
cd artifact/paper-results
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

python bin/generate_pash_vs_hs_barplots.py
python bin/mispeculation.py
python bin/open_heavy.py
python bin/varying_window.py
python bin/python_performance_plot.py
```

Representative outputs are written under `artifact/paper-results/img/`:

1. Overall hS/PaSh performance: `img/hs_pash_plot.pdf`.
2. Mis-speculation and execution trace: `img/execution_and_misspeculation.pdf`.
3. I/O-heavy and open-heavy overheads: `img/open_heavy.pdf`.
4. Varying speculation window sizes: `img/varying_window_sizes.pdf`.
5. Python frontend speedups: `img/python_speedup_bar.pdf`.

See [artifact/paper-results/README.md](artifact/paper-results/README.md) for
the mapping from scripts and input data files to paper figures.

**Full shell benchmark reruns:** Use a Docker-enabled host for full reruns. Some
benchmark setup/run scripts execute directly on the host, while others build and
launch their own benchmark-specific Docker images. The main entry points are:

```text
report/README.md
report/all_benchmarks
report/run_benchmark.py
report/benchmarks/*/setup
report/benchmarks/*/run
```

The paper uses presentation names, while the repository keeps several original
workload directory names. Use this crosswalk when moving from a paper result to
an artifact benchmark:

| Paper reference | Benchmark directory | Notes |
| --- | --- | --- |
| Benchmark summary row 1: TERA-Seq | `report/benchmarks/teraseq` | Dataset-specific runs are under `teraseq/<dataset>/`. |
| Benchmark summary row 2: Genomics | `report/benchmarks/bio4` | The artifact keeps the original Bio4 workflow name. |
| Benchmark summary row 3: Sklearn | `report/benchmarks/sklearn_large` | Paper-scale KDD99 run. `report/benchmarks/sklearn` is a smaller Docker sanity benchmark. |
| Benchmark summary row 4: DGSH | `report/benchmarks/dgsh` | Individual DGSH scripts are subdirectories such as `dgsh/1` and `dgsh/17`. |
| Benchmark summary row 5: NLP | `report/benchmarks/nlp` | Scaled/input-size variants include `nlp10x`, `nlp100x`, `nlp1000x`, `nlp1m`, `nlp10m`, and `nlp100m`. |
| Benchmark summary row 6: NOAA | `report/benchmarks/max_temp` | NOAA max-temperature workload. |
| Benchmark summary row 7: Unix50 | `report/benchmarks/unix_50` | Full and inflated inputs are under `unix_50/full*`. |
| Benchmark summary row 8: COVID-mts | `report/benchmarks/bus-analytics` | The artifact name follows the original transit/bus analytics workload. |
| Benchmark summary row 9: LogAnalysis | `report/benchmarks/log-analysis` | Size variants are `small`, `medium`, and `full`. |
| Benchmark summary row 10: WebIndex | `report/benchmarks/web-index` | Web-index input variants are under `web-index/web-index*`. |
| Benchmark summary row 11: microbenchmarks | `report/benchmarks/micro`, `report/benchmarks/micro_try` | Microbenchmark result data is also included under `artifact/paper-results/data/`. |

The Python frontend paper table maps to:

| Paper reference | Benchmark directory |
| --- | --- |
| Python row 1: BioAlign | `python_hs/report/benchmarks/biostars-multiprocessing` |
| Python row 2: ProteinInt | `python_hs/report/benchmarks/bioinfo-automine` |
| Python row 3: AudioProc | `python_hs/report/benchmarks/nemo-audio-processing` |
| Python row 4: VideoProc | `python_hs/report/benchmarks/rainbowcake-python-video-processing` |
| Python row 5: MRIanalysis | `python_hs/report/benchmarks/kaggle-captk-brats-preprocessing` |

Set the common environment variables:

```sh
export PASH_SPEC_TOP="$(pwd)"
export PASH_TOP="$PASH_SPEC_TOP"
export ORCH_TOP="$PASH_SPEC_TOP"
mkdir -p report/resources report/output
```

Docker is recommended for reproducibility, but it may slow down hS's sandboxing
and filesystem-heavy paths by roughly 10-20% compared with the paper's native
CloudLab setup. Use Docker results primarily to validate trends and scripts;
use CloudLab-like native hosts for final performance numbers.

Then run the relevant benchmark setup script to fetch or prepare inputs, followed
by a benchmark `run` script. The standard Docker benchmark pipeline is:

1. Build the base image from the repository root: `docker build -t hs .`
2. Run `./report/benchmarks/<bench>/setup`.
3. Run `./report/benchmarks/<bench>/<optional-subbenchmark>/run`.

Benchmark-level setup scripts such as `report/benchmarks/sklearn/setup` build
benchmark Docker images on top of the local `hs:latest` base image; they do not
replace the explicit base-image build step. Examples:

```sh
# Sklearn sanity benchmark. The paper-scale Sklearn row is sklearn_large.
docker build -t hs .
./report/benchmarks/sklearn/setup
./report/benchmarks/sklearn/run --target both --window 16
python3 report/summarize_results.py

# NOAA max-temperature benchmark, tiny input slice.
report/benchmarks/max_temp/inner/setup
report/benchmarks/max_temp/inner/tiny/run --target both --window 16

# DGSH benchmark 1.
report/benchmarks/dgsh/inner/setup
report/benchmarks/dgsh/inner/1/run --target both --window 16

# Bus analytics benchmark, full default input.
report/benchmarks/bus-analytics/inner/setup
report/benchmarks/bus-analytics/inner/full/run --target both --window 16

# Bio4 benchmark, small input.
report/benchmarks/bio4/inner/small/setup
report/benchmarks/bio4/inner/small/run --target both --window 16
```

The common flags are:

* `--target both`: run `/bin/sh`, run hS, and compare outputs.
* `--target sh-only`: run only the shell baseline.
* `--target hs-only`: run only hS.
* `--window N`: set the hS speculation window size.
* `--log enable|disable`: include or suppress hS debug logging.

Most shell benchmark runs write raw outputs, logs, and timing files under
`report/output/<benchmark>/`. The Docker wrapper prints the host output
directory at the end of each run and refreshes
`report/output/results_summary.csv`. The summary CSV has one row per benchmark
output directory, including shell time, hS time, window, target, and relative
speedup. You can regenerate it at any time with:

```sh
python3 report/summarize_results.py
```

To run the full list in `report/all_benchmarks`, use:

```sh
docker build -t hs .
./report/setup_all_benchmarks.sh
./report/run_all_benchmarks.sh --target both --window 16 --log disable
python3 report/summarize_results.py
```

This is the expensive path. Budget before launching. The run-time estimates
below are for representative paper-scale runs from the benchmark summary; using
`--target both` runs both `/bin/sh` and hS and therefore takes longer than one
baseline run.

| Benchmark scope | Approximate setup time | Approximate run time | Extra storage | Notes |
| --- | ---: | ---: | ---: | --- |
| `sklearn` smoke example | minutes after base image exists | a few minutes | <5 GB | Good Docker sanity check; not the paper-scale Sklearn row. |
| Sklearn, `sklearn_large` | minutes to 30 minutes | about 7 minutes | 1-5 GB | Paper-scale KDD99/scikit-learn benchmark. |
| Genomics, `bio4` | hours | about 1.3 hours | about 100 GB | Downloads selected 1000 Genomes BAMs. |
| DGSH, `dgsh` | minutes to 1 hour | <1 second to 40 minutes per script | 15-30 GB | Multiple scripts and inflated input variants. |
| NLP, `nlp*` | 1-3 hours | 10 seconds to 20 minutes per script | 80-100 GB | Gutenberg mirror plus scaled/input-size variants. |
| NOAA, `max_temp` | 1-2 hours | about 40 minutes | 80-100 GB | Four NOAA decade archives; tiny/small/medium/large variants exist. |
| Unix50, `unix_50` | 30-90 minutes | about 40 seconds for the paper row | about 25 GB | Full and inflated inputs are under `unix_50/full*`. |
| COVID-mts, `bus-analytics` | 30 minutes to 2 hours | about 6 minutes | 15-30 GB | Downloads the Athens telemetry archive and derives 100M/10G inputs. |
| LogAnalysis, `log-analysis` | 15-60 minutes | about 17 minutes | 5-20 GB | World Cup web-log data; small/medium/full variants. |
| WebIndex, `web-index` | 30 minutes to 2 hours | about 6 minutes | 10-30 GB | Wikipedia/web-index inputs and derived variants. |
| Microbenchmarks, `micro`, `micro_try` | minutes | seconds to minutes | <5 GB | Synthetic overhead and stress tests. |
| Riker suite | hours | hours | tens of GB | Artifact-only stress suite that builds many project images. |
| TERA-Seq, `teraseq` | about 6 hours | 25 minutes to 8 hours per workflow | about 500 GB | Requires large public sequencing datasets and substantial local disk. |
| Full `report/all_benchmarks` list | many hours to days | many hours to days | 500 GB or more | Intended for dedicated machines, not a quick AE smoke test. |

TERA-Seq and Riker-style benchmarks have their own Docker-heavy workflows:

```sh
report/benchmarks/teraseq/inner/setup.sh
report/benchmarks/teraseq/inner/<dataset>/run

report/benchmarks/riker/setup
report/benchmarks/riker/run
```

**Python frontend reruns:** The Python frontend prototype and benchmark scripts
are in `python_hs/` and `python_hs/report/`. Precomputed Python frontend results
used by the paper are included at:

```text
artifact/paper-results/data/python_hs_results.json
```

See [python_hs/report/README.md](python_hs/report/README.md) for benchmark setup
notes. Several Python benchmarks require external tools, large public datasets,
Kaggle credentials, or hours of runtime.

**Known limitations:** Full paper-result reproduction is hardware-sensitive and
expensive. The artifact therefore includes precomputed results and plotting
scripts for inspectability, plus permanent dataset links for reruns. The Python
frontend is a prototype; the OSDI '26 smoke test focuses on the shell artifact.

# Safety, Privacy, And Single-Blind Review

hS is an experimental systems artifact. It uses tracing, sandboxing, OverlayFS,
and cgroup facilities. Native execution may adjust writable cgroup files when
permissions allow. Run the artifact on a disposable VM or test machine if this
is a concern.

The artifact does not include analytics or reviewer tracking.

# Contact

For questions or bug reports, contact the paper authors through the
OSDI artifact-evaluation discussion channel.
