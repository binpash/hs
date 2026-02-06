#!/bin/bash

## Speculative-only JIT runtime for pash-spec
##
## Assumes the following variable is set:
## pash_spec_command_id: the node id for the specific command

##
## (1) Save shell state
##
export pash_previous_exit_status="$?"
export pash_previous_set_status=$-
source "$RUNTIME_DIR/pash_set_from_to.sh" "$pash_previous_set_status" "${DEFAULT_SET_STATE:-huB}"
pash_redir_output echo "$$: (1) Pre-ec, pre-set, jit-set: ($pash_previous_exit_status, $pash_previous_set_status, $-)"

##
## (2) Speculative execution - ask scheduler
##
export pash_speculative_command_id=$pash_spec_command_id
source "$RUNTIME_DIR/speculative_runtime.sh"

## Exit with the result
(exit "$pash_runtime_final_status")
