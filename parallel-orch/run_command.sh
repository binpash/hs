#!/bin/bash

## TODO: Not sure if it is OK and ideal to give this a string
export CMD_STRING=${1?No command was given to execute}
export TRACE_FILE=${2?No trace file path given}
export EXEC_MODE=${3?No execution mode given}

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
    "${PASH_SPEC_TOP}/overlay-sandbox/run-sandboxed.sh" "${PASH_SPEC_TOP}/parallel-orch/template_script_to_execute_in_overlay.sh"
else
    echo "In standard mode"
    "${PASH_SPEC_TOP}/parallel-orch/template_script_to_execute_in_overlay.sh"
fi


