#!/bin/bash
IN1=$IN_PRE/1.txt
# 1.2: extract names and sort
cat $IN1 | head -n 2 | cut -d ' ' -f 2

