#!/bin/bash
IN4=$IN_PRE/4.txt
# 4.5: 4.4 + pawns
cat $IN4 | tr ' ' '\n' | grep 'x' | grep '\.' | cut -d '.' -f 2 | cut -c 1-1 | tr '[a-z]' 'P' | sort | uniq -c | sort -nr

