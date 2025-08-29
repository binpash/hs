#!/usr/bin/env bash

# to directory of test.sh
cd -- "$( dirname -- "${BASH_SOURCE[0]}" )"

python -m unittest discover -s . -t .. "$@"
