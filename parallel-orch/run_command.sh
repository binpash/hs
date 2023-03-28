#!/bin/bash

## TODO: Not sure if it is OK and ideal to give this a string
export CMD_STRING=${1?No command was given to execute}
export TRACE_FILE=${2?No trace file path given}
export EXEC_MODE=${3?No execution mode given}
export CMD_ID=${4?No command id given}

source "$PASH_TOP/compiler/orchestrator_runtime/speculative/pash_spec_init_setup.sh"

if [ "sandbox" == "$EXEC_MODE" ]; then
    export sandbox_flag=1
elif [ "standard" == "$EXEC_MODE" ]; then
    export sandbox_flag=0
else
    echo "$$: Unknown value ${EXEC_MODE} for execution mode" 1>&2
    exit 1
fi

echo "Execution mode: $EXEC_MODE"

if [ $sandbox_flag -eq 1 ]; then
    ## Generate a temporary directory to store the workfiles
    echo "In sandbox mode"
    mkdir -p /tmp/pash_spec
    export SANDBOX_DIR="$(mktemp -d /tmp/pash_spec/sandbox_XXXXXXX)/"
    "${PASH_SPEC_TOP}/overlay-sandbox/run-sandboxed.sh" "${PASH_SPEC_TOP}/parallel-orch/template_script_to_execute_in_overlay.sh" "${SANDBOX_DIR}"
else
    echo "In standard mode"
    export SANDBOX_DIR=""
    "${PASH_SPEC_TOP}/parallel-orch/template_script_to_execute.sh"
fi

## Send a message to the scheduler socket
## Assumes "${PASH_SPEC_SCHEDULER_SOCKET}" is set and exported

## TODO: Pass the proper exit code
exit_code=0
msg="CommandExecComplete:${CMD_ID}|Exit code:${exit_code}|Sandbox dir:${SANDBOX_DIR}"
daemon_response=$(pash_spec_communicate_scheduler_just_send "$msg") # Blocking step, daemon will not send response until it's safe to continue
