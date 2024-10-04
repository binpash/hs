#!/bin/sh

export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
dir="${PASH_SPEC_TOP}"/report/timing/$(date +"%Y-%m-%dT%H-%M-%S")
mkdir -p $dir

printf "teraseq,sh_time,hs_time\n" >> $dir/teraseq.csv
for f in 5TERA 5TERA-short 5TERA3 TERA3 Akron5Seq mouse_SIRV RiboSeq dRNASeq RNASeq
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/teraseq/$f/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/teraseq/$f/hs_time)\n" >> $dir/teraseq.csv
done

printf "max_temp,sh_time,hs_time\n" >> $dir/max_temp.csv
printf ",$(cat ${PASH_SPEC_TOP}/report/output/max_temp/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/max_temp/hs_time)\n" >> $dir/max_temp.csv

printf "bio4,sh_time,hs_time\n" >> $dir/bio4.csv
for size in small medium large
do
	printf "$size,$(cat ${PASH_SPEC_TOP}/report/output/bio4/$size/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/bio4/$size/hs_time)\n" >> $dir/bio4.csv
done

printf "bio-ex,sh_time,hs_time\n" >> $dir/bio-ex.csv
for t in ex1 ex2 ex2-accelerated
do
	printf "$t,$(cat ${PASH_SPEC_TOP}/report/output/$t/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/$t/hs_time)\n" >> $dir/bio-ex.csv
done

printf "unix_50,sh_time,hs_time\n" >> $dir/unix_50.csv
printf ",$(cat ${PASH_SPEC_TOP}/report/output/unix_50/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/unix_50/hs_time)\n" >> $dir/unix_50.csv

printf "dgsh,sh_time,hs_time\n" >> $dir/dgsh.csv
for f in 1 2 3 4 5 6 7 8 9 17 18
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/dgsh/$f/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/dgsh/$f/hs_time)\n" >> $dir/dgsh.csv
done

printf "bus-analytics,sh_time,hs_time\n" >> $dir/bus-analytics.csv
printf ",$(cat ${PASH_SPEC_TOP}/report/output/bus-analytics/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/bus-analytics/hs_time)\n" >> $dir/bus-analytics.csv

printf "riker,sh_time,hs_time\n" >> $dir/riker.csv
for f in autoconf calc coreutils llvm lsof lua make memcached protobuf redis sqlite vim xz xz-clang
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/$f/baseline_time),$(cat ${PASH_SPEC_TOP}/report/output/$f/hs_time)\n" >> $dir/riker.csv
done

printf "git_tests,sh_time,hs_time\n" >> $dir/git_tests.csv
for f in $(cat ${PASH_SPEC_TOP}/report/benchmarks/git-tests/hs_passing_tests.txt)
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/git-tests/${f}.sh_time),$(cat ${PASH_SPEC_TOP}/report/output/git-tests/${f}.hs_time)\n" >> $dir/git_tests.csv
done

printf "wicked_cool_shell_scripts,sh_time,hs_time\n" >> $dir/wicked_cool_shell_scripts.csv
for f in 27 28 29 35 37 40 41 42 43 48 50 51 52 102
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/wicked_cool_shell_scripts/$f/result_sh_time 2>/dev/null),$(cat ${PASH_SPEC_TOP}/report/output/wicked_cool_shell_scripts/$f/result_hs_time 2>/dev/null)\n" >> $dir/wicked_cool_shell_scripts.csv
done

printf "log-analysis-wc,sh_time,hs_time\n" >> $dir/log-analysis-wc.csv
printf ",$(cat ${PASH_SPEC_TOP}/report/output/log-analysis/wc/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/log-analysis/wc/hs_time)\n" >> $dir/log-analysis-wc.csv

printf "nlp,sh_time,hs_time\n" >> $dir/nlp.csv
for f in 1_1 2_1 2_2 3_1 3_2 3_3 4_3 4_3b 6_1 6_1_1 6_1_2 6_2 6_3 6_4 6_5 6_7 7_1 7_2 8_1 8.2_1 8.2_2 8.3_2 8.3_3
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/nlp/${f}_sh_time),$(cat ${PASH_SPEC_TOP}/report/output/nlp/${f}_hs_time)\n" >> $dir/nlp.csv
done

printf "sklearn,sh_time,hs_time\n" >> $dir/sklearn.csv
for f in sklearn sklearn_large
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/sklearn/$f/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/sklearn/$f/hs_time)\n" >> $dir/sklearn.csv
done

printf "web-index,sh_time,hs_time\n" >> $dir/web-index.csv
printf ",$(cat ${PASH_SPEC_TOP}/report/output/web-index/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/web-index/hs_time)\n" >> $dir/web-index.csv

printf "fully_seq,sh_time,hs_time\n" >> $dir/fully_seq.csv
printf ",$(cat ${PASH_SPEC_TOP}/report/output/fully_seq/sh_time),$(cat ${PASH_SPEC_TOP}/report/output/fully_seq/hs_time)\n" >> $dir/fully_seq.csv

printf "micro,sh_time,hs_time\n" >> $dir/micro.csv
for f in 100echos 100echos2 giant_file giant_file2 multi_files 100echos2 giant_file giant_file2 multi_files
do
	printf "$f,$(cat ${PASH_SPEC_TOP}/report/output/micro/${f}.sh_time),$(cat ${PASH_SPEC_TOP}/report/output/micro/${f}.hs_time)\n" >> $dir/micro.csv
done
