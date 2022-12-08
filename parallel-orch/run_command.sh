#!/bin/bash

## TODO: Not sure if it is OK and ideal to give this a string
export CMD_STRING=${1?No command was given to execute}
export TRACE_FILE=${2?No trace file path given}

## Generate a temporary directory to store the workfiles
mkdir -p /tmp/pash_spec
export SANDBOX_DIR="$(mktemp -d /tmp/pash_spec/sandbox_XXXXXXX)/"

## Change into the sandbox directory (normally, we just want to save Riker working files there)
cd "$SANDBOX_DIR"
echo $CMD_STRING > "$SANDBOX_DIR/Rikerfile"

## Call Riker to execute the command
rkr --show
## Call Riker to get the trace
## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
rkr trace -o "$TRACE_FILE"
