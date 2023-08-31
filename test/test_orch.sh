#!/bin/bash

export ORCH_TOP=${ORCH_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export WORKING_DIR="$ORCH_TOP/test"
export TEST_SCRIPT_DIR="$WORKING_DIR/test_scripts"
export MISC_SCRIPT_DIR="$WORKING_DIR/misc"

echo "==================| Scheduler Tests |==================="
echo "Test directory:               $WORKING_DIR"
echo "Test script directory:        $TEST_SCRIPT_DIR"

## Set the DEBUG env variable to see detailed output
DEBUG=${DEBUG:-0}

bash="bash"
## Debug needs to be set to 2 because otherwise repetitions cannot be checked
orch="$ORCH_TOP/pash-spec.sh -d 2"
# Generated test scripts are saved here
test_dir_orch="$ORCH_TOP/test/test_scripts_orch"
test_dir_bash="$ORCH_TOP/test/test_scripts_bash"
# Test script output is saved here
output_dir_orch="$ORCH_TOP/test/output_orch"
output_dir_bash="$ORCH_TOP/test/output_bash"
# Results saved here
output_dir="$ORCH_TOP/test/results"

echo "Bash scripts saved at:       $test_dir_bash"
echo "Orch scripts saved at:       $test_dir_orch"
echo "Results saved at:            $output_dir"
echo "========================================================"

# Clear previous test results
rm -rf "$output_dir"
mkdir -p "$output_dir"
touch "$output_dir/result_status"

cleanup()
{
    # clear Riker's cache
    rm -rf ./.rkr
    rm -rf "$output_dir_orch"
    rm -rf "$output_dir_bash"
    mkdir "$output_dir_orch"
    mkdir "$output_dir_bash"
}

test_repetitions()
{
    local repetitions="$1"
    local exec_log_file="$2"
    if [ "${#repetitions}" -eq 1 ]; then
        result=`python3 $WORKING_DIR/parse_cmd_repetitions.py "--total" $exec_log_file`
        if [ "$repetitions" != "$result" ]; then
            echo " (!) Reps (total) not optimal: Expected: $repetitions | Got: $result" 1>&2
            return 1
        fi
    else
        result=`python3 $WORKING_DIR/parse_cmd_repetitions.py "--detailed" $exec_log_file`
        if [ "$repetitions" != "$result" ]; then
            echo " (!) Reps (detailed) not optimal: Expected: $repetitions | Got: $result" 1>&2
            return 1
        fi
    fi
}

run_test()
{
    cleanup
    local test=$1
    local repetitions="$2"

    if [ "$(type -t $test)" != "function" ]; then
        echo "$test is not a function!   FAIL"
        return 1
    fi

    echo -n "Running $test..."
    # Run test with bash
    output_diff=0
    export test_output_dir="$WORKING_DIR/output_bash"
    $test "$bash" "$TEST_SCRIPT_DIR" "$test_output_dir"  > "$test_output_dir/stdout" 2> /dev/null
    test_bash_ec=$?

     # Run test with orch
    export test_output_dir="$WORKING_DIR/output_orch"
    stderr_file="$(mktemp)"
    ## Print stderr
    if [ $DEBUG -ge 1 ]; then 
        $test "$orch" "$TEST_SCRIPT_DIR" "$test_output_dir"  2>&1 > "$test_output_dir/stdout" | tee "$stderr_file" 1>&2
        test_orch_ec=$?
    else
        $test "$orch" "$TEST_SCRIPT_DIR" "$test_output_dir"  2>"$stderr_file" > "$test_output_dir/stdout"
        test_orch_ec=$?
    fi

    diff -q "$WORKING_DIR/output_bash/" "$WORKING_DIR/output_orch/" > /dev/null
    test_diff_ec=$?
    # Test repetitions
    if [ ! -z "$repetitions" ]; then
        test_repetitions "$repetitions" "$stderr_file"
        test_repetitions_ec=$?
    else
        test_repetitions_ec=0
    fi

    ## Check if the two exit codes are both success or both error
    test $test_bash_ec == $test_orch_ec 
    test_ec=$?
    if [ $test_diff_ec -ne 0 ]; then
        echo -n " (!) output mismatch "
        diff "$WORKING_DIR/output_bash/" "$WORKING_DIR/output_orch/"
    else
        ## TODO: Don't have an else branch here (to show all errors at once)
        if [ $test_ec -ne 0 ]; then
            echo -n " (!) EC mismatch [$test_bash_ec-$test_orch_ec]"
            output_diff=1

        else
            echo -ne '\t\t\t'
        fi
    fi
    if [ $test_repetitions_ec -ne 0 ]; then
        echo -n " (!) Repetitions mismatch"
    fi
    if [ $test_diff_ec -ne 0 ] || [ $output_diff -ne 0 ] || [ $test_repetitions_ec -ne 0 ]; then
        echo "$test are not identical" >> $output_dir/result_status
        echo -e '\t\tFAIL'
        return 1
    else
        echo "$test are identical" >> $output_dir/result_status
        echo -e '\tOK'
        return 0
    fi
}

test_single_command()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > "$3/in1"
    $shell $2/test_single_command.sh
}

test1_1()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > "$3/in1"
    $shell $2/test1_1.sh
}

test1_2()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > "$3/in1"
    $shell $2/test1_2.sh
}

test1_3()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > "$3/in1"
    $shell $2/test1_3.sh
}

test2_1()
{
    local shell=$1
    $shell $2/test2_1.sh
}

test2_2()
{
    local shell=$1
    $shell $2/test2_2.sh
}

test2_3()
{
    local shell=$1
    $shell $2/test2_3.sh
}

test3_1()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in2
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in3
    $shell "$2/test3_1.sh"
}

test3_2()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in2
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in3
    $shell "$2/test3_2.sh"
}

test3_3()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in2
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in3
    $shell "$2/test3_3.sh"
}

test4_1()
{
    local shell=$1
    echo 'hello1' > "$3/in1"
    echo 'hello2' > "$3/in2"
    $shell "$2/test4_1.sh"
}

test4_2()
{
    local shell=$1
    echo 'hello1' > "$3/in1"
    echo 'hello2' > "$3/in2"
    $shell "$2/test4_2.sh"
}

test4_3()
{
    local shell=$1
    echo 'hello1' > "$3/in1"
    echo 'hello2' > "$3/in2"
    $shell "$2/test4_3.sh"
}

test5_1()
{
    local shell=$1
    echo 'hello1' > "$3/in1"
    echo 'hello2' > "$3/in2"
    $shell "$2/test5_1.sh"
}

test5_2()
{
    local shell=$1
    echo 'hello1' > "$3/in1"
    echo 'hello2' > "$3/in2"
    $shell "$2/test5_2.sh"
}

test5_3()
{
    local shell=$1
    echo 'hello1' > "$3/in1"
    echo 'hello2' > "$3/in2"
    $shell "$2/test5_3.sh"
}

test6()
{
    local shell=$1
    $shell "$2/test6.sh"
}

test7_1()
{
    local shell=$1
    $shell "$2/test7_1.sh"
}

test7_2()
{
    local shell=$1
    $shell "$2/test7_2.sh"
}

test7_3()
{
    local shell=$1
    $shell "$2/test7_3.sh"
}

test8()
{
    local shell=$1
    $shell "$2/test8.sh"
}

test9_1()
{
    local shell=$1
    $shell "$2/test9_1.sh"
}

test9_2()
{
    local shell=$1
    $shell "$2/test9_2.sh"
}

test9_3()
{
    local shell=$1
    $shell "$2/test9_3.sh"
}

test_stdout()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > "$3/in1"
    $shell $2/test_stdout.sh
}

test_loop()
{
    local shell=$1
    $shell $2/test_loop.sh
}

test_break()
{
    local shell=$1
    $shell $2/test_break.sh
}

test_network_access_1()
{
    local shell=$1
    $shell $2/test_network_access_1.sh
}

test_network_access_2()
{
    local shell=$1
    $shell $2/test_network_access_2.sh
}

test_network_access_3()
{
    local shell=$1
    $shell $2/test_network_access_3.sh
}

test_local_vars_1()
{
    local shell=$1
    $shell $2/test_local_vars_1.sh
}

test_local_vars_2()
{
    local shell=$1
    $shell $2/test_local_vars_2.sh
}

test_local_vars_3()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in2
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in3
    $shell $2/test_local_vars_3.sh
}

test_command_var_assignments_1(){
    local shell=$1
    $shell $2/test_command_var_assignments_1.sh
}

test_command_var_assignments_2(){
    local shell=$1
    $shell $2/test_command_var_assignments_2.sh
}


## TODO: make more loop tests with nested loops and commands after the loop

# We run all tests composed with && to exit on the first that fails
if [ "$#" -eq 0 ]; then 
    run_test test_single_command
    run_test test_local_vars_1
    run_test test_local_vars_2
    run_test test_local_vars_3
    run_test test_command_var_assignments_1
    run_test test_command_var_assignments_2
    run_test test1_1 # "1 2 3 1" # 7
    run_test test1_2 #"1 2 2 1" # 6
    run_test test1_3 #"1 2 2 1" # 6
    run_test test2_1 #"1 1 1 1 1 1 1 1 1 1 1" # 10
    run_test test2_2 #"1 1 1 1 1 1 1 1 1 1 1" # 10
    run_test test2_3 #"1 1 1 1 1 1 1 1 1 1 1" # 10
    run_test test3_1 # "1 1 2 1 2" # 7
    run_test test3_2 # "1 1 2 1 2" # 7
    run_test test3_3 # "1 1 2 1 3" # 8
    run_test test4_1 #"1 2 1" # 4
    run_test test4_2 #"1 2 1" # 4
    run_test test4_3 #"1 2 1" # 4
    run_test test5_1 #"1 1 1" # 3
    run_test test5_2 #"1 1 1" # 3
    run_test test5_3 #"1 1 1" # 3
    # run_test test6
    run_test test7_1 #"1 1 1 1 1 1 1 1 1 1 1 1" # 12
    run_test test7_2 #"1 1 1 1 1 1 1 1 1 1 1 1" # 12
    run_test test7_3 #"1 1 1 1 1 1 1 1 1 1 1 1" # 12

    # for now we don't check for reps in tests 9_x
    run_test test9_1 # "1 2 1 1 1 2 2 2 2 2 1 1 1" # 19
    run_test test9_2 # "1 1 1 1 1 1 1 1 1 1 1 1 1" # 13
    run_test test9_3 # "1 1 1 1 1 1 1 1 2 2 1 1 1" # 15
    run_test test_stdout #"1 1 1 1 1 1" # 6
    run_test test_loop
    run_test test_break
    run_test test_network_access_1 #"1 2 2"
    run_test test_network_access_2 #"1 2 2 2"
    run_test test_network_access_3 #"1 2 2 2"
else
    for testname in $@
    do
        run_test "$testname" "$2"
    done
fi

if type lsb_release > /dev/null ; then
   distro=$(lsb_release -i -s)
elif [ -e /etc/os-release ] ; then
   distro=$(awk -F= '$1 == "ID" {print $2}' /etc/os-release)
fi

distro=$(printf '%s\n' "$distro" | LC_ALL=C tr '[:upper:]' '[:lower:]')
# do different things depending on distro
case "$distro" in
    freebsd*)  
        # change sed to gsed
        sed () {
            gsed $@
        }
        ;;
    *)
        ;;
esac

echo -e "\n====================| Test Summary |====================\n"
echo "> Below follow the identical outputs:"
grep "are identical" "$output_dir"/result_status | awk '{print $1}' | tee $output_dir/passed.log

echo "> Below follow the non-identical outputs:"     
grep "are not identical" "$output_dir"/result_status | awk '{print $1}' | tee $output_dir/failed.log >> results_all.log
echo "========================================================"
TOTAL_TESTS=$(cat "$output_dir"/result_status | wc -l | xargs)
PASSED_TESTS=$(grep -c "are identical" "$output_dir"/result_status)
echo "Summary: ${PASSED_TESTS}/${TOTAL_TESTS} tests passed." | tee $output_dir/results.log
echo "========================================================"
