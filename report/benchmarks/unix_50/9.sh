#!/bin/bash
IN4=$IN_PRE/4.txt
# 4.3: find pieces captured by Belle with a pawn
cat $IN4 | tr ' ' '\n' | grep 'x' | grep '\.' | cut -d '.' -f 2 | grep -v '[KQRBN]' | wc -l

