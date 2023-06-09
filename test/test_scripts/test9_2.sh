# Tests simple directory creation 
# using mkdir -p

"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 0 "$test_output_dir/1/2/3/4"
"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 0.1 "$test_output_dir/1/2"
"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 0.3 "$test_output_dir/1/3"
"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 0.5 "$test_output_dir/1/3/4/5"
"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 0.7 "$test_output_dir/1/2/3/4/5"
"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 1.1 "$test_output_dir/1/2/3/4/5"
"$MISC_SCRIPT_DIR/sleep_and_mkdir_p.sh" 1.3 "$test_output_dir/1/2/3/4/5/6"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 1.7 "hello1" "$test_output_dir/1/1.txt"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 2.3 "hello2" "$test_output_dir/1/3/2.txt"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 2.7 "hello3" "$test_output_dir/1/3.txt"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 3 "hello4" "$test_output_dir/1/2/3/4/4.txt"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 3.6 "hello5" "$test_output_dir/1/2/3/4/5/5.txt"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 4 "hello6" "$test_output_dir/1/2/3/4/5/6/6.txt"
