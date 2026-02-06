#!/bin/bash

sudo apt-get update
# TODO: some of these are Riker dependencies are no longer needed.
sudo apt install -y make git python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs strace python3-venv

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash/src/pash}

## Download submodule dependencies
git submodule update --init --recursive

# Install try
(cd deps/try; ./setup.sh)

## Install PaSh (only needed for preprocessor and Python libraries)
## Note: NEW PaSh requires Python 3.12+. On some systems, `python` is 3.12 while `python3` is older.
## We create the venv manually with `python` to ensure we use 3.12+, then PaSh's setup will skip venv creation.
(cd deps/pash; ./scripts/distro-deps.sh)

# Find Python 3.12+
PASH_PYTHON=""
for py in python python3 python3.12; do
    if command -v "$py" &> /dev/null; then
        version=$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 12 ]; then
            PASH_PYTHON="$py"
            echo "Found Python 3.12+: $PASH_PYTHON ($version)"
            break
        fi
    fi
done

if [ -z "$PASH_PYTHON" ]; then
    echo "Error: Python 3.12+ required but not found. Please install Python 3.12 or later."
    exit 1
fi

# Use absolute path for venv
PASH_VENV="$PASH_SPEC_TOP/deps/pash/python_pkgs"

# Create venv with the correct Python version before running PaSh setup
if [ ! -d "$PASH_VENV" ]; then
    echo "Creating virtual environment with $PASH_PYTHON at $PASH_VENV..."
    "$PASH_PYTHON" -m venv "$PASH_VENV"
    if [ ! -f "$PASH_VENV/bin/pip" ]; then
        echo "Error: Failed to create virtual environment. pip not found at $PASH_VENV/bin/pip"
        exit 1
    fi
fi

# Upgrade pip and install PaSh dependencies manually (skip setup-pash.sh venv creation)
echo "Upgrading pip..."
"$PASH_VENV/bin/pip" install --upgrade pip

echo "Installing PaSh and dependencies..."
"$PASH_VENV/bin/pip" install -e "$PASH_SPEC_TOP/deps/pash"

## Install psutil for parallel-orch scheduler
echo "Installing psutil..."
"$PASH_VENV/bin/pip" install psutil

# Generate input files for tests (from setup-pash.sh)
echo "Generating input files..."
"$PASH_SPEC_TOP/deps/pash/evaluation/tests/input/setup.sh"

## Build fd_util for speculative execution
(cd parallel-orch; make)
