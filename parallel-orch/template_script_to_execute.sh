#!/bin/bash

## TODO: Pass frontier flag here instead of separate scripts

## Clean up the riker directory
## KK 2023-05-04 should this be done somewhere else? Could this interfere with overlay fs?
## TODO: Can we just ask riker to use a different cache (or put the cache to /dev/null)
##       since we never really want it to take the cache into account
rm -rf ./.rkr

## Save the script to execute in the sandboxdir
echo $CMD_STRING > ./Rikerfile
# cat ./Rikerfile 1>&2 # only for debugging

## Save the output shell variables to a file (to pass to the outside context)
## TODO: Currently pash_declare_vars doesn't work because riker invokes /bin/sh
##       which is bash in POSIX mode.
# echo 'bash "$RUNTIME_DIR/pash_declare_vars.sh" "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# TODO: There is a bug here and parsing of RW dependencies doesn't really work
#       when we add the following line.
echo 'declare -p > "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# echo 'cat "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# cat Rikerfile
## The (frontier) cmd is run outside a sandbox
## so we want to run and trace everything normally
# rkr --no-inject # --frontier
if [ $sandbox_flag -eq 1 ]; then
    rkr
else
    rkr --frontier
fi
exit_code="$?"

rkr --debug trace -o "$TRACE_FILE" > /dev/null
pash_redir_output echo "Sandbox ${CMD_ID} Output variables saved in: $OUTPUT_VARIABLE_FILE"

(exit $exit_code)
