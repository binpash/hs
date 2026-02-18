#!/bin/bash
base=$(dirname $0)
source ${base}/python_pkgs/bin/activate
exec "$@"
