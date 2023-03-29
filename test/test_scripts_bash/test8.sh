# tests successfull scheduling of Riker stopped cmds

echo "hello1" > ./output_bash/out1
ping localhost -c 5 -q | head -1 > ./output_bash/out1
ping localhost -c 5 -q | head -1 > ./output_bash/out2
ping localhost -c 3 -q | head -1 > ./output_bash/out3
ping localhost -c 1 -q | head -1 > ./output_bash/out1
