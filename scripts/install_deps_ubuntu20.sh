#!/bin/bash

sudo apt-get update
# TODO: some of these are Riker dependencies are no longer needed.
sudo apt install -y make git python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs strace python3-venv python3-pip

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

## Download submodule dependencies (try only - deps/pash removed)
git submodule update --init --recursive deps/try

## Build fd_util and set-diff for speculative execution
(cd executor; make)

## Install Python dependencies for preprocessor
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

# Create virtual environment for Python dependencies
PASH_VENV="$PASH_SPEC_TOP/python_pkgs"
if [ ! -d "$PASH_VENV" ]; then
    echo "Creating virtual environment with $PASH_PYTHON at $PASH_VENV..."
    "$PASH_PYTHON" -m venv "$PASH_VENV"
    if [ ! -f "$PASH_VENV/bin/pip" ]; then
        echo "Error: Failed to create virtual environment. pip not found at $PASH_VENV/bin/pip"
        exit 1
    fi
fi

# Upgrade pip
echo "Upgrading pip..."
"$PASH_VENV/bin/pip" install --upgrade pip

# Install preprocessor dependencies from requirements.txt
echo "Installing Python dependencies for preprocessor..."
"$PASH_VENV/bin/pip" install -r "$PASH_SPEC_TOP/requirements.txt"

# Verify installation
echo "Verifying Python dependencies..."
"$PASH_VENV/bin/python" -c "import shasta; import libdash; import libbash" || {
    echo "ERROR: Failed to install Python dependencies"
    exit 1
}

echo "✓ Python dependencies installed successfully"


