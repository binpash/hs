#!/bin/bash

## TODO: Export PASH_SPEC_TOP
## TODO: Export PASH_TOP


## TODO: Move this file to the other repo

## Only for debugging

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
## Generate a temporary directory to store the workfiles
mkdir -p /tmp/pash_spec

## Create a temporary directory where PaSh-Spec can use for temporary files and logs
export PASH_SPEC_TMP_PREFIX="$(mktemp -d /tmp/pash_spec/pash_XXXXXXX)/"

export PASH_SPEC_SCHEDULER_SOCKET="${PASH_SPEC_TMP_PREFIX}/scheduler_socket"


"$PASH_TOP/pa.sh" --speculative "$@"
