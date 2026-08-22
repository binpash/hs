#!/bin/sh

window=15

## hs writes its own logs to <name>.hs.log; <name>.hs.out then holds only what
## the script itself printed, so it can be diffed against the sh baseline.
hs_run() {
    name=$1
    script=$2
    /usr/bin/time -o "$name.hs.time" -f %e ../../../hs -d2 --window "$window" \
        --jit-log "$name.hs.log" --scheduler-log "$name.hs.log" \
        --preprocessor-log "$name.hs.log" --internal-log "$name.hs.internal.log" \
        "$script" > "$name.hs.out" 2>&1
}

sh_run() {
    name=$1
    script=$2
    /usr/bin/time -o "$name.sh.time" -f %e sh "$script" > "$name.sh.out" 2>&1
}

hs_run 100echos2 100echos2.sh
hs_run 100echos 100echos.sh
hs_run giant_file.100 giant_file.sh
hs_run giant_file.10000 giant_file2.sh
hs_run multi_files 100echos2.sh

sh_run 100echos2 100echos2.sh
sh_run 100echos 100echos.sh
sh_run giant_file.100 giant_file.sh
sh_run giant_file.10000 giant_file2.sh
sh_run multi_files 100echos2.sh
