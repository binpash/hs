#!/bin/bash

export LATEST_ENV_FILE
export POST_EXEC_ENV
export CMD_STRING

RUN=$(printf 'source $LATEST_ENV_FILE; %s; exit_code=$?; source $RUNTIME_DIR/pash_declare_vars.sh $POST_EXEC_ENV; exit $exit_code' "${CMD_STRING}")
strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $TRACE_FILE bash -c "$RUN"

