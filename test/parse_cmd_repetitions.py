#!/bin/env python3
import sys
import re

#1: Log file produced by orch. 

with open(sys.argv[1], "r", encoding="UTF8") as f:
    lines = f.read().split("\n")
REGEX = re.compile(r"TRACE\|.*\|Executions\|")
lines = list(filter(REGEX.match, lines))
lines = [line.split("|")[4] for line in lines]
print(" ".join(lines))
