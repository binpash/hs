#!/usr/bin/env bash

# to directory of test.sh
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"

python3 -m unittest discover -s . -t .. "$@"
