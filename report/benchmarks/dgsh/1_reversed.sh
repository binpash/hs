#!/bin/bash

## Initialize the necessary temporary files
file1=$(mktemp)
cat $INPUT_FILE >"$file1"
printf 'File type:\t'
file - <"$file1"

printf 'Original size:\t'
wc -c <"$file1"

printf 'gzip:\t\t'
gzip -c <"$file1" | wc -c

printf 'bzip2:\t\t'
bzip2 -c <"$file1" | wc -c

printf 'xz:\t\t'
xz -c <"$file1" | wc -c
