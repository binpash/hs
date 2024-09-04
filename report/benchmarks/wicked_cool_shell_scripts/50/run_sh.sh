mkdir sh
touch -d "2 days ago" sh/file
echo test=1 > sh/rotatelogs.conf
./50.sh > result_sh_out
