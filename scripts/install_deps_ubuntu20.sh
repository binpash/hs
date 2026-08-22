#!/bin/bash

sudo apt-get update
# TODO: some of these are Riker dependencies are no longer needed.
sudo apt install -y make git python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs strace python3-venv python3-pip

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}

## Download submodule dependencies (try only - deps/pash removed)
git submodule update --init --recursive deps/try

## Build fd_util and set-diff for speculative execution
(cd executor; make)

## Sandbox base: a dedicated top-level directory holding the per-run overlay
## upperdirs/workdirs (see executor/executor_util.py). It must not live under
## any directory that try overlays (/tmp, /home, ...), hence top-level.
HS_SANDBOX_BASE="${HS_SANDBOX_BASE:-/hs-sandbox}"
if [ ! -d "$HS_SANDBOX_BASE" ]; then
    echo "Creating sandbox base $HS_SANDBOX_BASE..."
    sudo mkdir -m 1777 "$HS_SANDBOX_BASE"
fi
## tmpfs keeps sandbox copy-ups off the disk; skip silently if already mounted.
if ! mountpoint -q "$HS_SANDBOX_BASE"; then
    sudo mount -t tmpfs -o mode=1777 tmpfs "$HS_SANDBOX_BASE" || \
        echo "Warning: could not tmpfs-mount $HS_SANDBOX_BASE; sandboxes will be disk-backed (slower but correct)"
fi
echo "Note: the tmpfs mount does not persist across reboots. For persistence add to /etc/fstab:"
echo "  tmpfs $HS_SANDBOX_BASE tmpfs mode=1777 0 0"

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


