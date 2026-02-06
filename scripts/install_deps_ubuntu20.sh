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
(cd deps/pash; ./scripts/distro-deps.sh; ./scripts/setup-pash.sh)

## Install psutil for parallel-orch scheduler
source deps/pash/python_pkgs/bin/activate
pip install psutil
deactivate

## Build fd_util for speculative execution
(cd parallel-orch; make)
