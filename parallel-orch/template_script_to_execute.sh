#!/bin/bash

export LATEST_ENV_FILE
export POST_EXEC_ENV
export CMD_STRING
strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $TRACE_FILE bash -c 'source $LATEST_ENV_FILE; $CMD_STRING; exit_code=$?; source $RUNTIME_DIR/pash_declare_vars.sh $POST_EXEC_ENV; exit $exit_code'

