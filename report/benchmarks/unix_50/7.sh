#!/bin/bash
IN4=$IN_PRE/4.txt
# 4.1: find number of rounds
cat $IN4 | tr ' ' '\n' | grep '\.' | wc -l

