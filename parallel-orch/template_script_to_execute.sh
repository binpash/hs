#!/bin/bash

if [ "speculate" == "$EXEC_MODE" ]; then
    echo 1000 > /proc/$$/oom_score_adj
fi

# Magic, don't touch without consulting Di
RUN=$(printf 'source %s; %s\n exit_code=$?; source $RUNTIME_DIR/pash_declare_vars.sh %s; trap - EXIT; exit $exit_code' "${LATEST_ENV_FILE}" "${CMD_STRING}" "${POST_EXEC_ENV}")
strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $TRACE_FILE env -i bash -c "$RUN"
