# Tests speculation of completely independent cmds

"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.33 "hello0" "$test_output_dir/out0"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.3  "hello1" "$test_output_dir/out1"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.27 "hello2" "$test_output_dir/out2"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.2  "hello3" "$test_output_dir/out3"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.25 "hello4" "$test_output_dir/out4"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.18 "hello5" "$test_output_dir/out5"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.12 "hello6" "$test_output_dir/out6"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.1  "hello7" "$test_output_dir/out7"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.0  "hello8" "$test_output_dir/out8"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.22 "hello9" "$test_output_dir/out9"
"$MISC_SCRIPT_DIR/sleep_and_echo.sh" 0.05 "hello10" "$test_output_dir/out10"
