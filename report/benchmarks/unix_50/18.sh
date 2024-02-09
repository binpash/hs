#!/bin/bash
IN8=$IN_PRE/8.txt
# 8.1: count unix birth-year
cat $IN8 | tr ' ' '\n' | grep 1969 | wc -l

