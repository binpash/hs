# tests successfull scheduling of Riker stopped cmds

echo "hello1" > "$test_output_dir/out1"
ping localhost -c 5 -q | head -1 > "$test_output_dir/out1"
ping localhost -c 5 -q | head -1 > "$test_output_dir/out2"
ping localhost -c 3 -q | head -1 > "$test_output_dir/out3"
ping localhost -c 1 -q | head -1 > "$test_output_dir/out1"
