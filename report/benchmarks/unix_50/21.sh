#!/bin/bash
IN8=$IN_PRE/8.txt
# 8.4: find longest words without hyphens
cat $IN8 | tr -c "[a-z][A-Z]" '\n' | sort | awk "length >= 16"

