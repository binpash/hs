#!/bin/bash
IN1=$IN_PRE/1.txt
# 1.1: extract names and sort
cat $IN1 | cut -d ' ' -f 2 | sort

