#!/bin/bash

## Install Riker's dependencies
sudo apt install -y make clang llvm git gcc python3-cram file graphviz
sudo update-alternatives --install /usr/bin/cram cram /usr/bin/cram3 100

## Install Riker
(git submodule update --init --recursive; cd deps/riker; make; sudo make install)
