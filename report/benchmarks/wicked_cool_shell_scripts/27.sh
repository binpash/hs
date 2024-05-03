#!/bin/bash

# 27 Displaying a File with Line Numbers
# There are several ways to add line numbers to a displayed file, many of
# which are quite short. For example, here’s one solution using awk:
# awk '{ print NR": "$0 }' < inputfile
# On some Unix implementations, the cat command has an -n flag, and
# on others, the more (or less, or pg) pager has a flag for specifying that each
# line of output should be numbered. But on some Unix flavors, none of
# these methods will work, in which case the simple script in Listing 4-1 can
# do the job.
# The Code


# numberlines--A simple alternative to cat -n, etc.
for filename in "$@"; do
    linecount="1"
    while IFS=$'\n' read -r line; do
        echo "${linecount}: $line"
        linecount="$(( $linecount + 1 ))"
    done < $filename
done
