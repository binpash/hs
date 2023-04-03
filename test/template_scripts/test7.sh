# Tests simple directory creation 
# using mkdir of 
# simple directories

sleep 0.5 | mkdir "$test_output_dir/1"
sleep 0.1 | mkdir "$test_output_dir/2"
sleep 0.4 | mkdir "$test_output_dir/1/3"
sleep 0.3 | mkdir "$test_output_dir/1/3/4"
sleep 0.2 | mkdir "$test_output_dir/1/3/4/5"
sleep 1   | mkdir "$test_output_dir/1/2/3"
