#!/bin/bash

## Save the script to execute in the sandboxdir
echo $CMD_STRING > ./Rikerfile

## Call Riker to execute the command
# rkr --debug --log all --show
rkr --show
## TODO: Run with gdb for debugging
## ```sh
# gdb rkr
## (gdb) break wrappers.hh:readlink
## (gdb) run --debug --log all --show
## (gdb) print std::string::max_size()
## ```
## Call Riker to get the trace
## TODO: Normally we would like to plug in Riker and get the actual Trace data structure
rkr --debug trace -o "$TRACE_FILE"

## Failing test case:
## CMD_STRING="./test/misc/append_a_line.sh" ./overlay-sandbox/run-sandboxed.sh ./parallel-orch/template_script_to_execute_in_overlay.sh