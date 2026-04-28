## hS — Out-of-order shell-script execution

### Overview

`hs` is a system for executing shell scripts out of order. It achieves this by tracing a script's speculative execution; if an error occurs, for example due to dependencies between components executed out of order, `hs` re-executes only the necessary parts to ensure correct outcomes. The project aims to boost the parallel execution of shell scripts, reducing their runtime and enhancing efficiency.

### Security Warning

Being an experimental project, `hs` currently uses sudo to change permission of `/sys/fs/cgroup/cgroup.procs` to 666 (which by default is usually 644).

### Structure

The project's top-level directory contains the following:

- `deps`: Dependencies required by `hs`.
- `docs`: Documentation and architectural diagrams.
- `model-checking`: Tools and utilities for model checking.
- `scheduler`: Scheduler daemon — manages speculative execution order and dependency tracking.
- `executor`: Executor — runs commands in sandboxes with tracing.
- `jit_runtime`: JIT runtime — shell scripts sourced during execution for state management.
- `preprocessor`: Preprocessor — transforms shell ASTs for speculative execution.
- `README.md`: This documentation file.
- `report`: Generated reports related to test runs and performance metrics.
- `requirements.txt`: List of Python dependencies.
- `Rikerfile`: Configuration file for Riker.

### Installation

`binpash-hs` is a Linux-only package and requires Python 3.12 or later.
The runtime also relies on standard Linux system tools such as `bash`, `gcc`,
`make`, `libtool`, `libtool-bin`, `autoconf`, `automake`, `m4`, `pkg-config`,
`strace`, `util-linux`, `netcat-openbsd`, `attr`, and `mergerfs`. Installing
from the sdist also needs the matching Python development headers, for example
`python3.12-dev` on Ubuntu.

After the package is published, install it with:

```sh
uv tool install --python 3.12 binpash-hs
```

If using `pip`, invoke it through Python 3.12 or newer. A system `pip` attached
to Python 3.10 will hide this package because the package metadata declares
`Requires-Python: >=3.12`.

```sh
python3.12 -m pip install binpash-hs
```

To test a release uploaded to TestPyPI, use TestPyPI for `binpash-hs` and real
PyPI for dependencies:

```sh
python3.12 -m venv /tmp/binpash-hs-testpypi
. /tmp/binpash-hs-testpypi/bin/activate
python -m pip install --upgrade pip
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  binpash-hs
```

For local testing from a source checkout:

```sh
git clone https://github.com/binpash/hs
cd hs
git submodule update --init --recursive deps/try
./scripts/install_deps_ubuntu20.sh
```

To build the PyPI artifacts locally:

```sh
scripts/prepare_pypi_package.sh
```

That script cleans local build directories, ensures the `deps/try` submodule is
present, builds the sdist and Linux wheel, runs `twine check`, and scans the
archives for paper/artifact data that should not be published. Add
`--install-tool --install-sudo-wrapper --smoke` to reinstall the built wheel
locally and run a short smoke check.

For PyPI/TestPyPI publishing, upload the sdist printed by the script. The
generated `linux_x86_64` wheel is intended for local validation; PyPI rejects
raw Linux wheel tags unless they are repaired/tagged as manylinux or musllinux.

### Running `hs`

The installed command is `hs`. It sets up the hS runtime, launches the scheduler
daemon, preprocesses the input script, and executes it with speculative
execution.

Examples:

```sh
hs --help
sudo "$(command -v hs)" -c 'echo hello'
sudo "$(command -v hs)" script_to_speculatively_run.sh
```

`uv tool install` places `hs` in the user's local bin directory. Many systems
configure `sudo` with a restricted `secure_path`, so `sudo hs ...` may fail even
when `hs ...` is on the user's `PATH`. Use `sudo "$(command -v hs)" ...`, or
install a root-visible wrapper:

```sh
sudo ln -sf "$(command -v hs)" /usr/local/bin/hs
```

From a source checkout, use `./hs` instead. `pash-spec.sh` is kept as a
compatibility wrapper.

Important options include:

- `-c, --command COMMAND`: execute a command string instead of a script file.
- `-d, --debug LEVEL`: set the debug level.
- `--log_file FILE`: write runtime logs to a file.
- `--window N`: set the speculative window size.

### Testing

For an installed package, run:

```sh
sudo "$(command -v binpash-hs-test)"
```

From a source checkout, run:

```sh
sudo ./test/test_orch.sh
sudo DEBUG=2 ./test/test_orch.sh 2>logs.txt
```

### Contributing and Further Development

Contributions are always welcome! The project roadmap includes extending the architecture to support complete scripts, optimizing the scheduler for better performance, etc.

For a detailed description of possible optimizations, see the [related issues](https://github.com/binpash/dynamic-parallelizer/issues?q=is%3Aopen+is%3Aissue+label%3Aoptimization)

### License

`hs` is licensed under the MIT License. See the `LICENSE` file for more information.
