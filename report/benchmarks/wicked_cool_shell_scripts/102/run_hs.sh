for i in $(seq 0 100)
do
    touch $i.jpg
done

./102.sh jpg png > result_hs_out
./102.sh png jpg >> result_hs_out
