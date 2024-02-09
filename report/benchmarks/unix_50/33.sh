#!/bin/bash
IN10=$IN_PRE/10.txt
# 10.2: list Turing award recipients while working at Bell Labs
cat $IN10 | sed 1d | grep 'Bell' | cut -f 2

