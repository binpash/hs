#!/bin/bash

# TODO: There is a bug here and parsing of RW dependencies doesn't really work
#       when we add the following line.
# echo 'declare -p > "$OUTPUT_VARIABLE_FILE"' >> ./Rikerfile

touch "$TEMPDIR/Rikerfile"

if [ $NEW_ENV_FILE != "None" ]; then
    source $NEW_ENV_FILE 1>&2
    echo "source $NEW_ENV_FILE" >> "$TEMPDIR/Rikerfile"
fi

## Save the script to execute in the sandboxdir
echo $CMD_STRING >> "$TEMPDIR/Rikerfile"
echo "Riker env: $RIKER_ENV_FILE" 1>&2

## Add command to export Riker's environment variables after run is complete to a file
echo "source $RUNTIME_DIR/pash_declare_vars.sh $RIKER_ENV_FILE" >> "$TEMPDIR/Rikerfile"

## Save the current (latest) env to a file (before Riker is run)
source "$RUNTIME_DIR/pash_declare_vars.sh" "$LATEST_ENV_FILE"

if [ $speculate_flag -eq 1 ]; then
    rkr_cmd="rkr"
else
    rkr_cmd="rkr --frontier"
fi

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
