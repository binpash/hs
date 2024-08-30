set -x
window=16
pashcmd="/srv/hs/pash-spec.sh --window $window"

##### -- 27 -- #####
echo running experiment 27
cd 27
./27.sh test >out_sh
$pashcmd ./27.sh test >out_hs
diff out_sh out_hs
if [ $? -eq 0 ]; then
    echo OK
else
    echo FAIL
fi
