#!/bin/bash

if [ "speculate" == "$EXEC_MODE" ]; then
    echo 1000 > /proc/$$/oom_score_adj
fi

# Magic, don't touch without consulting Di
## PASH_REDIR is re-pointed AFTER sourcing the env file (which restores the
## caller's value, i.e. the real log file). Writing the real log inside the
## sandbox would both put it in the traced write set (making concurrent
## speculations conflict on it) and commit a stale copy over the real file.
## run_command.sh exports the per-node target (a bind-mounted file under
## /tmp/pash_spec), which is inherited here and baked into the run string
## because `env -i` strips the environment.
RUN=$(printf 'source %s 2>/dev/null; PASH_REDIR=%s; %s\n exit_code=$?; hs_runtime_tmp_args=("$@")\n hs_set_options_cmd="$(set +o)"; source ${RUNTIME_DIR}/pash_declare_vars.sh %s; trap - EXIT; exit $exit_code' "${LATEST_ENV_FILE}" "${PASH_REDIR}" "${CMD_STRING}" "${POST_EXEC_ENV}")
# NOTE: tracing happens OUTSIDE this script — fstrace wraps the whole `try`
# invocation in run_command.sh. Here we just run the command in the sandbox.
env -i bash -c "$RUN"
