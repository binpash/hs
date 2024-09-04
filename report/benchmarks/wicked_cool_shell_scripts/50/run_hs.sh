mkdir hs
touch -d "2 days ago" hs/file
echo test=1 > hs/rotatelogs.conf
./50.sh > result_hs_out
