#!/bin/bash

export ASSIGNMENT_STRING=${1?No assignment was given to execute}
export PRE_ENV_FILE=${2?No env file to run with given}
export POST_EXEC_ENV=${3?No Riker env file given}

source "$PASH_TOP/compiler/orchestrator_runtime/speculative/pash_spec_init_setup.sh"

source "${ASSIGNMENT_STRING}"
"${ASSIGNMENT_STRING}"
source $RUNTIME_DIR/pash_declare_vars.sh "${POST_EXEC_ENV}"
