mkdir log
touch -d "2 days ago" log/file
echo h > log/file
echo file=1 > log/rotatelogs.conf
./50.sh > result_hs_out
mv log hs
