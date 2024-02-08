#!/bin/bash
IN7=$IN_PRE/7.txt
# 7.1: identify number of AT&T unix versions
cat $IN7 | cut -f 1 | grep 'AT&T' | wc -l

