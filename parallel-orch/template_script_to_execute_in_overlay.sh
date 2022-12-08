#!/bin/bash

## Save the script to execute in the sandboxdir
echo $CMD_STRING > ./Rikerfile

## Call Riker to execute the command
rkr --debug --log all --show
## TODO: Run with gdb for debugging
## ```sh
## gdb rkr
## (gdb) run --debug --log all --show
## ```
## Call Riker to get the trace
## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
rkr --debug trace -o "$TRACE_FILE"
