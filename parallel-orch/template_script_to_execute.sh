#!/bin/bash

## TODO: Pass frontier flag here instead of separate scripts


## Save the script to execute in the sandboxdir
echo $CMD_STRING > ./Rikerfile
echo "$$: Rikerfile contents" 1>&2
wc ./Rikerfile 1>&2
cat ./Rikerfile 1>&2
## Save the output shell variables to a file (to pass to the outside context)
## TODO: Currently pash_declare_vars doesn't work because riker invokes /bin/sh
##       which is bash in POSIX mode.
# echo 'bash "$RUNTIME_DIR/pash_declare_vars.sh" "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# TODO: There is a bug here and parsing of RW dependencies doesn't really work
#       when we add the following line.
# echo 'env > "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# echo 'cat "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# cat Rikerfile
## The (frontier) cmd is run outside a sandbox
## so we want to run and trace everything normally
# rkr --no-inject # --frontier
rkr # --frontier
## TODO: Save the exit code here
rkr --debug trace -o "$TRACE_FILE" > /dev/null

## KK 2023-05-03 This probably causes the /dev/tty output (TODO: Check)
pash_redir_output echo "Sandbox ${CMD_ID} Output variables saved in: $OUTPUT_VARIABLE_FILE"
