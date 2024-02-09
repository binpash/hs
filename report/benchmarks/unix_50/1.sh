#!/bin/bash
IN1=$IN_PRE/1.txt
# 1.0: extract the last name
cat $IN1 | cut -d ' ' -f 2

