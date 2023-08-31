#!/bin/bash

# TODO: There is a bug here and parsing of RW dependencies doesn't really work
#       when we add the following line.
# echo 'declare -p > "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile

touch "$TEMPDIR/Rikerfile"

## We source the latest env file
## TODO: Executing through $RUNTIME_DIR/pash_source_declare_vars.sh fails. Figure out why.
echo "source $LATEST_ENV_FILE" > "$TEMPDIR/Rikerfile"

## Save the script to execute in the sandboxdir
echo $CMD_STRING >> "$TEMPDIR/Rikerfile"

## Add command to export Riker's environment variables after run is complete to a file
echo "source $RUNTIME_DIR/pash_declare_vars.sh $POST_EXEC_ENV" >> "$TEMPDIR/Rikerfile"

if [ $speculate_flag -eq 1 ]; then
    rkr_cmd="rkr"
else
    rkr_cmd="rkr --frontier"
fi

cat "$TEMPDIR/Rikerfile" 1>&2

$rkr_cmd --db "$TEMPDIR" --rikerfile "$TEMPDIR/Rikerfile"
exit_code="$?"

if [ "$exit_code" -eq 0 ]; then
    echo "first riker run done (Node: ${CMD_ID})" 1>&2
else
    echo "Riker error: first Riker command failed with EC $exit_code - (Node: ${CMD_ID})" 1>&2
fi

rkr --db "$TEMPDIR" --rikerfile "$TEMPDIR/Rikerfile" --debug trace -o "$TRACE_FILE" > /dev/null
echo 'second riker run done' 1>&2

(exit $exit_code)
