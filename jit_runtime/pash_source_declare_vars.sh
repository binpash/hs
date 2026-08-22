#!/bin/bash

## This sources variables that were produced from `declare -p`

## TODO: Fix this to not source read only variables
## TODO: Does this work with arrays

## TODO: Fix this to not source pash variables so as to not invalidate PaSh progress

## TODO: Fix this filtering

filter_vars_file()
{
    ## HS_JIT_LOG (and its descriptor) are filtered so a restored env can never
    ## redirect this shell's logging: a sandboxed execution runs with
    ## HS_JIT_LOG pointing at that node's private .jitlog, which must not leak
    ## back into the JIT shell through a post-env file.
    cat "$1" | grep -v "^declare -\([A-Za-z]\|-\)* \(pash\|PASH_OLD_IFS\|HS_JIT_LOG\|BASH\|LINENO\|EUID\|GROUPS\|cmd_exit_code\)"
    # The extension below is done for the speculative pash
    # | grep -v "LS_COLORS"
}

## TODO: Error handling if the argument is empty?
if [ "$PASH_DEBUG_LEVEL" -eq 0 ]; then
    > /dev/null 2>&1 source <(filter_vars_file "$1")
elif [ -n "${HS_JIT_LOG_FD:-}" ]; then
    >&"$HS_JIT_LOG_FD" 2>&"$HS_JIT_LOG_FD" source <(filter_vars_file "$1")
else
    >>"$HS_JIT_LOG" 2>&1 source <(filter_vars_file "$1")
fi
