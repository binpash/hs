#!/bin/bash

## JIT runtime for pash-spec speculative execution
##
## This script is sourced by the preprocessed shell script for each command.
## It saves the current shell state, communicates with the scheduler daemon,
## and either applies the scheduler's result or falls back to eval execution.
##
## Assumes the following variables are set:
##   pash_spec_command_id: the node id for the specific command
##   RUNTIME_DIR: path to jit_runtime directory
##   RUNTIME_LIBRARY_DIR: path to executor directory (for fd_util, set-diff)

###############################################################################
# Section 1: Save shell state
###############################################################################

## Save exit status and shell options
export pash_previous_exit_status="$?"
export pash_previous_set_status=$-
source "$RUNTIME_DIR/pash_set_from_to.sh" "$pash_previous_set_status" "${DEFAULT_SET_STATE:-huB}"
pash_redir_output echo "$$: (1) Pre-ec, pre-set, jit-set: ($pash_previous_exit_status, $pash_previous_set_status, $-)"

## Save IFS for proper restoration later
pash_redir_output echo "$$: [JIT] Before save - IFS=$(declare -p IFS 2>&1 || echo 'unset')"
if [ -z "${IFS+x}" ]; then
    unset PASH_OLD_IFS
else
    PASH_OLD_IFS="$IFS"
fi
pash_redir_output echo "$$: [JIT] Saved PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
IFS=$' \t\n'
pash_redir_output echo "$$: [JIT] After setting default - IFS=$(declare -p IFS 2>&1 || echo 'unset')"

## Save positional parameters and set options before they get overwritten by sourcing
## This is needed by pash_source_declare_vars.sh, because "source" messes up $@
hs_runtime_tmp_args=("$@")
hs_set_options_cmd="$(set +o)"
pash_redir_output echo "$$: [JIT] Saved positional parameters: ${hs_runtime_tmp_args[@]}"

###############################################################################
# Section 2: Save variables and communicate with scheduler
###############################################################################

export pash_speculative_command_id=$pash_spec_command_id

pash_redir_output echo "$$: (2) Before asking the scheduler for cmd: ${pash_speculative_command_id} exit code..."

## Save the shell variables to a file (necessary for expansion)
export pash_runtime_shell_variables_file="${PASH_TMP_PREFIX}/variables_$RANDOM$RANDOM$RANDOM"
unset cmd_exit_code
unset output_variable_file
unset stdout_file
set +u
pash_redir_output echo "$$: [JIT] Before restore for declare - IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
if [ -z "${PASH_OLD_IFS+x}" ]; then
    unset IFS
else
    IFS="$PASH_OLD_IFS"
fi
pash_redir_output echo "$$: [JIT] After restore, before pash_declare_vars - IFS=$(declare -p IFS 2>&1 || echo 'unset')"
source "$RUNTIME_DIR/pash_declare_vars.sh" "$pash_runtime_shell_variables_file"
pash_redir_output echo "$$: [JIT] After pash_declare_vars - IFS=$(declare -p IFS 2>&1 || echo 'unset')"
IFS=$' \t\n'
pash_redir_output echo "$$: [JIT] After setting default - IFS=$(declare -p IFS 2>&1 || echo 'unset')"
pash_redir_output echo "$$: (1) Bash variables saved in: $pash_runtime_shell_variables_file"
pash_redir_output echo "$$: [JIT] Contents of pash_runtime_shell_variables_file IFS/PASH_OLD_IFS lines:"
pash_redir_output grep -E "^declare.*IFS" "$pash_runtime_shell_variables_file" || pash_redir_output echo "  (no IFS declarations found)"

## Determine all current loop iterations and send them to the scheduler
pash_loop_iter_counters=${pash_loop_iters:-None}
pash_redir_output echo "$$: Loop node iteration counters: $pash_loop_iter_counters"

## Send and receive from scheduler daemon (blocking)
msg="Wait:${pash_speculative_command_id}|Loop iters:${pash_loop_iter_counters}|Variables file:${pash_runtime_shell_variables_file}"
daemon_response=$(pash_spec_communicate_scheduler "$msg")

###############################################################################
# Section 3: Handle scheduler response
###############################################################################

if [[ "$daemon_response" == *"OK:"* ]]; then
    # shellcheck disable=SC2206
    response_args=($daemon_response)
    pash_redir_output echo "$$: (2) Scheduler responded: $daemon_response"

    cmd_exit_code=${response_args[1]}
    output_variable_file=${response_args[2]}
    stdout_file=${response_args[3]}

    pash_redir_output echo "$$: (2) Recovering stdout from: $stdout_file"

    pash_redir_output echo "$$: (2) Recovering script variables from: $output_variable_file"
    pash_redir_output echo "$$: [JIT] Contents of output_variable_file IFS/PASH_OLD_IFS lines:"
    pash_redir_output grep -E "^declare.*IFS" "$output_variable_file" || pash_redir_output echo "  (no IFS declarations found)"
    pash_redir_output echo "$$: [JIT] Before pash_restore_fds - IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
    source "$RUNTIME_DIR/pash_restore_fds.sh" "${output_variable_file}.fds" "${stdout_file}"
    pash_redir_output echo "$$: [JIT] After pash_restore_fds - IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
    source "$RUNTIME_DIR/pash_source_declare_vars.sh" "$output_variable_file"
    pash_redir_output echo "$$: [JIT] After sourcing output_variable_file: IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"

elif [[ "$daemon_response" == *"UNSAFE:"* ]]; then
    pash_redir_output echo "$$: (2) Scheduler responded: $daemon_response"
    pash_redir_output echo "$$: (2) Executing command: $pash_speculative_command_id"
    ## Execute the command via eval fallback
    cmd="$(cat "$PASH_SPEC_NODE_DIRECTORY/$pash_speculative_command_id")"
    pash_redir_output echo "$$: [JIT] UNSAFE: Before restore for eval - IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
    if [ -z "${PASH_OLD_IFS+x}" ]; then
	unset IFS
    else
	IFS="$PASH_OLD_IFS"
    fi
    pash_redir_output echo "$$: [JIT] UNSAFE: After restore for eval - IFS=$(declare -p IFS 2>&1 || echo 'unset')"
    # shellcheck disable=SC2086
    eval "$cmd"
    cmd_exit_code=$?
elif [ -z "$daemon_response" ]; then
    ## Scheduler crashed
    pash_redir_output echo "$$: ERROR: (2) Scheduler crashed!"
    exit 1
else
    pash_redir_output echo "$$: ERROR: (2) Scheduler responded garbage ${daemon_response}!"
    exit 1
fi

###############################################################################
# Section 4: Cleanup and return exit code
###############################################################################

pash_redir_output echo "$$: (2) Scheduler returned exit code: ${cmd_exit_code} for cmd with id: ${pash_speculative_command_id}."

pash_runtime_final_status=${cmd_exit_code}
unset cmd_exit_code
unset output_variable_file
unset cmd
unset stdout_file

pash_redir_output echo "$$: [JIT] End of jit.sh - IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"

## Exit with the result
(exit "$pash_runtime_final_status")
