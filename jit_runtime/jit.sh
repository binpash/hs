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
## Save IFS for proper restoration in speculative_runtime.sh (matching fae47999 pattern)
##
pash_redir_output echo "$$: [JIT] Before save - IFS=$(declare -p IFS 2>&1 || echo 'unset')"
if [ -z "${IFS+x}" ]; then
    unset PASH_OLD_IFS
else
    PASH_OLD_IFS="$IFS"
fi
pash_redir_output echo "$$: [JIT] Saved PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
IFS=$' \t\n'
pash_redir_output echo "$$: [JIT] After setting default - IFS=$(declare -p IFS 2>&1 || echo 'unset')"

##
## (2) Speculative execution - ask scheduler
##
export pash_speculative_command_id=$pash_spec_command_id
source "$RUNTIME_DIR/speculative/speculative_runtime.sh"

##
## Restore IFS before returning to caller (matching fae47999 pattern)
##
pash_redir_output echo "$$: [JIT] Before restore - IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
if [ -z "${PASH_OLD_IFS+x}" ]; then
    unset IFS
else
    IFS="$PASH_OLD_IFS"
fi
pash_redir_output echo "$$: [JIT] After restore - IFS=$(declare -p IFS 2>&1 || echo 'unset')"

pash_redir_output echo "$$: [JIT] End of jit.sh (returning to caller) - IFS=$(declare -p IFS 2>&1 || echo 'unset')"

## Exit with the result
(exit "$pash_runtime_final_status")
