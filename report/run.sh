#!/bin/bash

BASE=$(dirname $(realpath "$0"))
HSTMP=/tmp/hs_tmp

for b in $(cat $BASE/koala_benchmarks); do bs=$(echo $b | cut -d '/' -f 1); $BASE/benchmarks/$bs/setup; done

mkdir -p $HSTMP
for b in $(cat $BASE/koala_benchmarks); do $BASE/benchmarks/$b/run $HSTMP --target hs-only; done
sudo rm -rf $HSTMP
