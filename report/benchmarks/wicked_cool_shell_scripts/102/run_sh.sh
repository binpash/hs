for i in $(seq 0 100)
do
    touch $i.jpg
done

./102.sh jpg png > result_sh_out
./102.sh png jpg >> result_sh_out
