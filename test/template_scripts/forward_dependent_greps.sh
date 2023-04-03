grep foo "$test_output_dir/in1" > "$test_output_dir/out1"
grep foo "$test_output_dir/out1" > "$test_output_dir/out2"
grep foo "$test_output_dir/out2" > "$test_output_dir/out3"
pwd
