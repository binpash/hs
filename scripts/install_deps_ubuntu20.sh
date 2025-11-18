#!/bin/bash

sudo apt-get update
# TODO: some of these are Riker dependencies are no longer needed.
sudo apt install -y make git python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs strace

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

## Fix permissions on .git/modules if needed
if [ -d .git/modules ]; then
    sudo chown -R $(whoami):$(whoami) .git/modules 2>/dev/null || true
fi

## Download submodule dependencies
if git submodule update --init --recursive; then
    echo "Submodules cloned successfully"
else
    SUBMODULE_ERROR=$?
    echo "Warning: git submodule failed (exit code: $SUBMODULE_ERROR). Attempting manual clone..."
    
    # Manual clone fallback
    if [ ! -d deps/pash/.git ]; then
        echo "Cloning deps/pash manually..."
        rm -rf deps/pash
        git clone -b spec_future https://github.com/binpash/pash.git deps/pash || {
            echo "Error: Failed to clone deps/pash"
            exit 1
        }
    else
        echo "deps/pash already exists"
    fi
    
    if [ ! -d deps/try/.git ]; then
        echo "Cloning deps/try manually..."
        rm -rf deps/try
        git clone -b hs https://github.com/binpash/try.git deps/try || {
            echo "Error: Failed to clone deps/try"
            exit 1
        }
    else
        echo "deps/try already exists"
    fi
fi

# Install try
if [ -f deps/try/setup.sh ]; then
    (cd deps/try; ./setup.sh)
else
    echo "Warning: deps/try/setup.sh not found. Skipping try installation."
fi

## Install PaSh
if [ -f deps/pash/scripts/distro-deps.sh ] && [ -f deps/pash/scripts/setup-pash.sh ]; then
    (cd deps/pash; ./scripts/distro-deps.sh; ./scripts/setup-pash.sh)
else
    echo "Warning: PaSh setup scripts not found. Skipping PaSh installation."
fi

python3 scripts/patch_pash.py
