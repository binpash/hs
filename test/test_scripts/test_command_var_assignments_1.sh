"$MISC_SCRIPT_DIR/sleep_and_grep.sh" 0.4 
"$MISC_SCRIPT_DIR/sleep_and_export.sh" 0.35 "foo" "hello"
"$MISC_SCRIPT_DIR/sleep_and_export.sh" 0.3 "bar" "world"
"$MISC_SCRIPT_DIR/sleep_and_export.sh" 0.25 "filename" "out1.txt"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.2 "$foo" "$test_output_dir/$filename"
"$MISC_SCRIPT_DIR/sleep_and_export.sh" 0.15 "foo" "hello"
"$MISC_SCRIPT_DIR/sleep_and_cat.sh" 0.1 "$test_output_dir/$filename" "$test_output_dir/out2"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.05 "$foo $bar" "$test_output_dir/out2"
