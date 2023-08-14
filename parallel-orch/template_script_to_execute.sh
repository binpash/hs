#!/bin/bash

## TODO: Pass speculate flag here instead of separate scripts

## Clean up the riker directory
## KK 2023-05-04 should this be done somewhere else? Could this interfere with overlay fs?
## TODO: Can we just ask riker to use a different cache (or put the cache to /dev/null)
##       since we never really want it to take the cache into account
# rm -rf ./.rkr

## Save the script to execute in the sandboxdir
echo $CMD_STRING > "$TEMPDIR/Rikerfile"
# cat ./Rikerfile 1>&2 # only for debugging

## Save the output shell variables to a file (to pass to the outside context)
## TODO: Currently pash_declare_vars doesn't work because riker invokes /bin/sh
##       which is bash in POSIX mode.
# echo 'bash "$RUNTIME_DIR/pash_declare_vars.sh" "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile
# TODO: There is a bug here and parsing of RW dependencies doesn't really work
#       when we add the following line.
echo 'declare -p > "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile

if [ $speculate_flag -eq 1 ]; then
    rkr_cmd="rkr"
else
    rkr_cmd="rkr --frontier"
fi

strace -o out $rkr_cmd --db "$TEMPDIR" --rikerfile "$TEMPDIR/Rikerfile"
echo 'first riker run done' 1>&2

exit_code="$?"

rkr --db "$TEMPDIR" --rikerfile "$TEMPDIR/Rikerfile" --debug trace -o "$TRACE_FILE" > /dev/null
echo 'second riker run done' 1>&2

(exit $exit_code)
