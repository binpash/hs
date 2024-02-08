#!/bin/bash
IN7=$IN_PRE/7.txt
# 7.2: find  most frequently occurring machine
cat $IN7 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1

