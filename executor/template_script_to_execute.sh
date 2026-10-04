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
##
## $? is set to the previous command's status (pash_previous_exit_status, which
## jit.sh records and the env file carries) right before the command, so a
## command that reads $? sees what it would in the real shell; `&& :` keeps a
## restored `set -e` from aborting on a nonzero value. The post env records
## this command's own status there, so the next speculated command's pre env
## carries the right $? too.
##
## The script's shell options are applied too (hs_set_options_cmd, from the
## env file). The command runs as `{ CMD } && :` so that under set -e a failing
## command does not end this shell before the post env is written; jit.sh
## applies errexit in the real shell. errexit is read from $-, because
## command substitution clears it: "$(set +o)" always reports it off.
RUN=$(printf 'source %s 2>/dev/null; HS_JIT_LOG=%s; unset HS_JIT_LOG_FD; eval "$hs_set_options_cmd"; (exit "${pash_previous_exit_status:-0}") && :; { %s\n } && :; exit_code=$?; export pash_previous_exit_status=$exit_code; hs_runtime_tmp_args=("$@")\n hs_set_options_cmd="$(set +o)"; case $- in *e*) hs_set_options_cmd=${hs_set_options_cmd/set +o errexit/set -o errexit};; esac; set +e; source ${RUNTIME_DIR}/pash_declare_vars.sh %s; trap - EXIT; exit $exit_code' "${LATEST_ENV_FILE}" "${HS_JIT_LOG}" "${CMD_STRING}" "${POST_EXEC_ENV}")
strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $TRACE_FILE env -i bash -c "$RUN"
