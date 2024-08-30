#!/bin/bash

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export SYSADMINDIR="${PASH_SPEC_TOP}/report/benchmarks/wicked_cool_shell_scripts"
export OUTBASE="${PASH_SPEC_TOP}/report/output/sysadmin/$EXPERIMENT"

cd "$SYSADMINDIR"

mkdir -p "$OUTBASE"

hs_r() {
	local experiment=$1
	local window=$2
	local log=$3

	echo Running hS test for $experiment with window $window

    cmd="sudo docker run --rm -it --privileged hs/sysadmin/$EXPERIMENT /srv/hs/pash-spec.sh --window $window"
	if [ "$log" = "enable" ]; then
		cmd="$cmd -d 2"
	fi
	cmd="$cmd /root/cmd"
	/usr/bin/time -f '%e' -o "$OUTBASE/hs_time" $cmd &> "$OUTBASE/hs_log"
}

sh_r() {
	local experiment=$1

	echo Running sh baseline for $experiment

    cmd="sudo docker run --rm -it --privileged hs/sysadmin/$EXPERIMENT /root/cmd"
	/usr/bin/time -f '%e' -o "$OUTBASE/hs_time" $cmd &> "$OUTBASE/sh_log"
}

usage() {
	echo "Usage: $0 [--window WINDOW_SIZE] [--target TARGET] [--log LOG_OPTION]"
	echo "  --window WINDOW_SIZE  Window experiment to run hs with (default: 5)"
	echo "  --target TARGET       Target to run: hs-only, sh-only, or both"
	echo "  --log LOG_OPTION      Whether to enable logging for hs: enable or disable (default: enable)"
	exit 1
}

window=5
target=""
log="enable"

while [ $# -gt 0 ]; do
	case "$1" in
		--window)
			window="$2"
			shift 2
			;;
		--target)
			target="$2"
			shift 2
			;;
		--log)
			log="$2"
			shift 2
			;;
		*)
			usage
			;;
	esac
done

if [ -z "$target" ]; then
	echo "Error: --target argument is required"
	usage
fi

run_hs=false
run_sh=false

case "$target" in
    hs-only)
        run_hs=true
        ;;
    sh-only)
        run_sh=true
        ;;
    both)
        run_hs=true
        run_sh=true
        ;;
esac

if $run_sh
then
sh_r $EXPERIMENT
fi

if $run_hs
then
hs_r $EXPERIMENT $window $log
fi
