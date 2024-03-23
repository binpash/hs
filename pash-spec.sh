#!/bin/bash

##
## This is the entry of pash-speculate and calls parallel-orch/orch.py
##

## Find the source code top directory
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

## Generate a temporary directory to store the workfiles
mkdir -p /tmp/pash_spec

## Delete any Riker cache
rm -rf ./.rkr

export PASH_SPEC_TMP_PREFIX=/tmp/pash_spec/pash_test
mkdir -p $PASH_SPEC_TMP_PREFIX
## Create a temporary directory where PaSh-Spec can use for temporary files and logs
# export PASH_SPEC_TMP_PREFIX="$(mktemp -d /tmp/pash_spec/pash_XXXXXXX)/"

## Initialize the scheduler-server
export PASH_SPEC_SCHEDULER_SOCKET="${PASH_SPEC_TMP_PREFIX}/scheduler_socket"

## TODO: Replace this with a call to pa.sh (which will start the scheduler on its own).
a=$1
shift
"$PASH_TOP/pa.sh" $a --speculative "$@"

