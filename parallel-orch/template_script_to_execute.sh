#!/bin/bash

strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $TRACE_FILE bash -c "source $LATEST_ENV_FILE; $CMD_STRING; source $RUNTIME_DIR/pash_declare_vars.sh $POST_EXEC_ENV"
exit_code=$?

(exit $exit_code)
