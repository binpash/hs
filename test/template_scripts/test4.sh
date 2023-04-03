# Tests that w/w dependencies get scheduled correctly

"$MISC_SCRIPT_DIR/sleep_and_cat.sh" 0.3 "$test_output_dir/in1" "$test_output_dir/out1"
cat "$test_output_dir/out1" > "$test_output_dir/out2"
"$MISC_SCRIPT_DIR/sleep_and_cat.sh" 0.6 "$test_output_dir/in2" "$test_output_dir/out1"