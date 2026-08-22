#!/bin/bash

if [ "speculate" == "$EXEC_MODE" ]; then
    echo 1000 > /proc/$$/oom_score_adj
fi

# Magic, don't touch without consulting Di
## HS_JIT_LOG is re-pointed AFTER sourcing the env file (which restores the
## caller's value). `env -i` strips the environment, so the value is baked into
## the run string. run_command.sh exports a per-node target next to the trace
## artifacts; both live under /tmp/pash_spec, which the dependency filter
## ignores, so the log never creates conflicts between speculated iterations.
## HS_JIT_LOG_FD is cleared for the same reason: hs's descriptors do not reach
## in here.
RUN=$(printf 'source %s 2>/dev/null; HS_JIT_LOG=%s; unset HS_JIT_LOG_FD; %s\n exit_code=$?; hs_runtime_tmp_args=("$@")\n hs_set_options_cmd="$(set +o)"; source ${RUNTIME_DIR}/pash_declare_vars.sh %s; trap - EXIT; exit $exit_code' "${LATEST_ENV_FILE}" "${HS_JIT_LOG}" "${CMD_STRING}" "${POST_EXEC_ENV}")
strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $TRACE_FILE env -i bash -c "$RUN"
