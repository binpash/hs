#!/bin/bash
IN93=$IN_PRE/9.3.txt
# 9.3: animal that used to decorate the Unix room
cat $IN93 | cut -c 1-2 | tr -d '\n'

