"$MISC_SCRIPT_DIR/sleep_and_grep.sh" 1 "foo" "$test_output_dir/in1" "$test_output_dir/out1"
"$MISC_SCRIPT_DIR/sleep_and_grep.sh" 0.6 "foo" "$test_output_dir/out1" "$test_output_dir/out2"
"$MISC_SCRIPT_DIR/sleep_and_grep.sh" 2 "foo" "$test_output_dir/out2" "$test_output_dir/out3"
pwd
