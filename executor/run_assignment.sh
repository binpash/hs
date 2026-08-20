#!/bin/bash

ASSIGNMENT_STRING=${1?No assignment was given to execute}
PRE_ENV_FILE=${2?No env file to run with given}
POST_EXEC_ENV=${3?No Riker env file given}

## Functions now exported from parent hs script, no need to source
# source "$PASH_SPEC_TOP/jit_runtime/pash_spec_init_setup.sh"

## The env file is a `declare -p` dump, so it carries hs's exported
## HS_JIT_LOG_FD back in even though the scheduler scrubbed it from our
## environment. That descriptor belongs to hs and is not open here, so clear it
## right after sourcing and let the JIT helpers append to HS_JIT_LOG by path.
RUN=$(printf 'source %s; unset HS_JIT_LOG_FD; %s\n source ${RUNTIME_DIR}/pash_declare_vars.sh %s' "${PRE_ENV_FILE}" "${ASSIGNMENT_STRING}" "${POST_EXEC_ENV}")

bash -c "$RUN"
