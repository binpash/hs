# Tests simple directory creation 
# using mkdir -p

sleep 1 | mkdir -p "$test_output_dir/1/2/3/4"
sleep 0.1 | mkdir -p  "$test_output_dir/1/2"
sleep 0.4 | mkdir -p  "$test_output_dir/1/3"
sleep 0.2 | mkdir -p  "$test_output_dir/1/3/4/5"
sleep 0.6 | mkdir "$test_output_dir/1/2/3/4/5"
sleep 0.3 | mkdir "$test_output_dir/1/2/3/4/5"
sleep 0 | mkdir "$test_output_dir/1/2/3/4/5/6"
