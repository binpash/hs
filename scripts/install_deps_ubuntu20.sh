#!/bin/bash

## Install Riker's dependencies
sudo apt-get update
sudo apt install -y make clang llvm git gcc python3-cram file graphviz libtool
sudo update-alternatives --install /usr/bin/cram cram /usr/bin/cram3 100

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

pip3 install --user -r $PASH_SPEC_TOP/requirements.txt

## Download submodule dependencies
git submodule update --init --recursive

## Install Riker
(cd deps/riker; make; sudo make install)

## Install PaSh
(cd deps/pash; ./scripts/distro-deps.sh; ./scripts/setup-pash.sh)
