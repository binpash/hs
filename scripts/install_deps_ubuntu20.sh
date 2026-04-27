#!/usr/bin/env bash
set -euo pipefail

if command -v sudo >/dev/null 2>&1; then
    SUDO=sudo
else
    SUDO=
fi

repo_top=$(git rev-parse --show-toplevel)
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$repo_top}
cd "$PASH_SPEC_TOP"

$SUDO apt-get update
$SUDO apt-get install -y \
    attr \
    autoconf \
    automake \
    bc \
    build-essential \
    bsdextrautils \
    ca-certificates \
    curl \
    expect \
    file \
    git \
    graphviz \
    jq \
    libcap2-bin \
    libffi-dev \
    libtool \
    m4 \
    make \
    mergerfs \
    netcat-openbsd \
    pkg-config \
    procps \
    software-properties-common \
    python3 \
    python3-cram \
    python3-matplotlib \
    python3-pip \
    python3-setuptools \
    python3-testresources \
    python3-venv \
    strace \
    util-linux \
    wget

ensure_python312_packages() {
    if apt-cache show python3.12-venv >/dev/null 2>&1; then
        $SUDO apt-get install -y python3.12 python3.12-venv
        return
    fi

    if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
    fi

    if [ "${ID:-}" = "ubuntu" ] && command -v add-apt-repository >/dev/null 2>&1; then
        echo "Python 3.12 packages were not found in the enabled apt repositories."
        echo "Adding the deadsnakes PPA to install python3.12 and python3.12-venv..."
        $SUDO add-apt-repository -y ppa:deadsnakes/ppa
        $SUDO apt-get update
    fi

    if apt-cache show python3.12-venv >/dev/null 2>&1; then
        $SUDO apt-get install -y python3.12 python3.12-venv
    fi
}

ensure_python312_packages

if ! command -v python3.12 >/dev/null 2>&1; then
    echo "Error: python3.12 is still unavailable after apt setup." >&2
    echo "Install Python 3.12+ and venv support manually, then rerun this script." >&2
    echo "On Ubuntu 20.04/22.04, the deadsnakes PPA is one common option:" >&2
    echo "  sudo add-apt-repository -y ppa:deadsnakes/ppa" >&2
    echo "  sudo apt-get update" >&2
    echo "  sudo apt-get install -y python3.12 python3.12-venv" >&2
    exit 1
fi

## Download submodule dependencies (try only - deps/pash removed)
git submodule update --init --recursive deps/try

## Build try helpers and hS helpers for speculative execution.
(cd deps/try/utils; make)
$SUDO install -m 0755 deps/try/utils/try-commit /usr/local/bin/try-commit
$SUDO install -m 0755 deps/try/utils/try-summary /usr/local/bin/try-summary
(cd executor; make)

## Install Python dependencies for the preprocessor and scheduler.
# shasta 0.5 uses Python 3.12 syntax, so the artifact requires Python 3.12+.
PASH_PYTHON=""
for py in python3.12 python3 python; do
    if command -v "$py" &> /dev/null; then
        version=$("$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 12 ]; then
            PASH_PYTHON="$py"
            echo "Found Python 3.12+: $PASH_PYTHON ($version)"
            break
        fi
    fi
done

if [ -z "$PASH_PYTHON" ]; then
    echo "Error: Python 3.12+ required but not found."
    echo "On Ubuntu 24.04, install it with:"
    echo "  sudo apt-get install -y python3.12 python3.12-venv"
    echo "On Ubuntu 20.04, install Python 3.12+ using your site's preferred package source or pyenv,"
    echo "and make sure the matching venv support is installed."
    exit 1
fi

# Create virtual environment for Python dependencies
PASH_VENV="$PASH_SPEC_TOP/python_pkgs"
if [ -d "$PASH_VENV" ] && [ ! -x "$PASH_VENV/bin/python" ]; then
    echo "Removing incomplete virtual environment at $PASH_VENV..."
    rm -rf "$PASH_VENV"
fi
if [ -x "$PASH_VENV/bin/python" ]; then
    venv_version=$("$PASH_VENV/bin/python" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    venv_major=$(echo "$venv_version" | cut -d. -f1)
    venv_minor=$(echo "$venv_version" | cut -d. -f2)
    if [ "$venv_major" -ne 3 ] || [ "$venv_minor" -lt 12 ]; then
        echo "Removing Python $venv_version virtual environment at $PASH_VENV; Python 3.12+ is required..."
        rm -rf "$PASH_VENV"
    fi
fi
if [ ! -d "$PASH_VENV" ]; then
    echo "Creating virtual environment with $PASH_PYTHON at $PASH_VENV..."
    "$PASH_PYTHON" -m venv "$PASH_VENV"
    if [ ! -f "$PASH_VENV/bin/pip" ]; then
        echo "Error: Failed to create virtual environment. pip not found at $PASH_VENV/bin/pip"
        echo "If using a non-default Python on Ubuntu, install the matching venv package."
        echo "For Python 3.12 this is usually python3.12-venv."
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
"$PASH_VENV/bin/python" -c "import shasta; import libdash; import libbash; import psutil" || {
    echo "ERROR: Failed to install Python dependencies"
    exit 1
}

echo "✓ Python dependencies installed successfully"
