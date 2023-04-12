#!/bin/bash

## Save the script to execute in the sandboxdir
echo $CMD_STRING > ./Rikerfile
## The (frontier) cmd is run outside a sandbox
## so we want to run and trace everything normally
rkr # --frontier
rkr --debug trace -o "$TRACE_FILE" > /dev/null
