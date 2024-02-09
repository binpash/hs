#!/bin/bash
IN5=$IN_PRE/5.txt
# 5.1: extract hello world
cat $IN5 | grep 'print' | cut -d "\"" -f 2 | cut -c 1-12

