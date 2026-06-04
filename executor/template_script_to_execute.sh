#!/bin/bash

if [ "speculate" == "$EXEC_MODE" ]; then
    echo 1000 > /proc/$$/oom_score_adj
fi

# Magic, don't touch without consulting Di
RUN=$(printf 'source %s 2>/dev/null; %s\n exit_code=$?; hs_runtime_tmp_args=("$@")\n hs_set_options_cmd="$(set +o)"; source ${RUNTIME_DIR}/pash_declare_vars.sh %s; trap - EXIT; exit $exit_code' "${LATEST_ENV_FILE}" "${CMD_STRING}" "${POST_EXEC_ENV}")
# NOTE: tracing happens OUTSIDE this script — fstrace wraps the whole `try`
# invocation in run_command.sh. Here we just run the command in the sandbox.
env -i bash -c "$RUN"
