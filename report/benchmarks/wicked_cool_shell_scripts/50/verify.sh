a=$(ls sh)
b=$(ls hs)

if [ "$a" != "$b" ]
then
    echo failed > results_error
fi
