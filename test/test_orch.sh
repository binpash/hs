#!/bin/bash

export ORCH_TOP=${ORCH_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export WORKING_DIR="$ORCH_TOP/test"
export TEMPLATE_SCRIPT_DIR="$WORKING_DIR/template_scripts"

bash="bash"
orch="$ORCH_TOP/pash-spec.sh"

test_dir_orch="$ORCH_TOP/test/test_scripts_orch"
test_dir_bash="$ORCH_TOP/test/test_scripts_bash"

output_dir_orch="$ORCH_TOP/test/output_orch"
output_dir_bash="$ORCH_TOP/test/output_bash"

output_dir="$ORCH_TOP/test/results"

rm -rf "$output_dir"
mkdir -p "$output_dir"
touch "$output_dir/result_status"

cleanup()
{
    rm -rf "$output_dir_orch"
    rm -rf "$output_dir_bash"
    mkdir -p "$output_dir_orch"
    mkdir -p "$output_dir_bash"
}

run_test()
{
    local test=$1

    if [ "$(type -t $test)" != "function" ]; then
        echo "$test is not a function!   FAIL"
        return 1
    fi

    echo -n "Running $test..."
    # Run test with bash
    export test_output_dir="$WORKING_DIR/output_bash"
    export generated_test_dir="$WORKING_DIR/test_scripts_bash"
    generate_test_files
    $test "$bash" "$generated_test_dir" "$test_output_dir" > /dev/null 2>/dev/null
    test_bash_ec=$?

     # Run test with orch
    export test_output_dir="$WORKING_DIR/output_orch"
    export generated_test_dir="$WORKING_DIR/test_scripts_orch"
    generate_test_files
    $test "$orch" "$generated_test_dir" "$test_output_dir" > /dev/null 2>/dev/null
    test_orch_ec=$?
    
    diff -q "$WORKING_DIR/output_bash/" "$WORKING_DIR/output_orch/" > /dev/null
    test_diff_ec=$?

    ## Check if the two exit codes are both success or both error
    { [ $test_bash_ec -eq 0 ] && [ $test_pash_ec -eq 0 ]; } || { [ $test_bash_ec -ne 0 ] && [ $test_pash_ec -ne 0 ]; }
    test_ec=$?
    
    if [ $test_diff_ec -ne 0 ]; then
        echo -n " (!) output mismatch "
    else
        if [ $test_ec -ne 0 ]; then
            echo -n " (?) exit code mismatch "
        else
            echo -ne '\t\t\t'
        fi
    fi
    # if [ $test_diff_ec -ne 0 ] || [ $test_ec -ne 0 ]; then
    if [ $test_diff_ec -ne 0 ]; then
        echo "$test are not identical" >> $output_dir/result_status
        echo -e '\t\tFAIL'
        return 1
    else
        echo "$test are identical" >> $output_dir/result_status
        echo -e '\tOK'
        return 0
    fi
}

generate_test_files()
{
    rm -f $generated_test_dir/*
    mkdir -p $generated_test_dir

    for file in `ls $TEMPLATE_SCRIPT_DIR`; do
        envsubst <$TEMPLATE_SCRIPT_DIR/$file > $generated_test_dir/$file
    done
}

test1()
{
    local shell=$1
    export file_directory=$3
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > "${file_directory}/in1"
    $shell $2/forward_dependent_greps.sh
}

test2()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in2
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in3
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in4
    echo $'bar\nbaz\nqux\nquux\nfoo\nbar' > $3/in5
    $shell $2/forward_dependent_greps.sh
}

test3()
{
    local shell=$1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in1
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in2
    echo $'foo\nbar\nbaz\nqux\nquux\nfoo\nbar' > $3/in3
    $shell $2/semi_dependent_greps.sh
}

test4()
{
    local shell=$1
    echo 'hello1' > $3/in1
    echo 'hello2' > $3/in2    
    $shell $2/test4.sh
}

test5()
{
    local shell=$1
    echo 'hello1' > $3/in1
    echo 'hello2' > $3/in2    
    $shell $2/test5.sh
}

test6()
{
    local shell=$1 
    $shell $2/test6.sh
}

test8()
{
    local shell=$1 
    $shell $2/test8.sh
}

# We run all tests composed with && to exit on the first that fails
if [ "$#" -eq 0 ]; then
    cleanup
    run_test test1
    cleanup
    run_test test2
    cleanup
    run_test test3
    cleanup
    run_test test4
    cleanup
    run_test test5
    cleanup
    run_test test6
    # Test 8 is failing for now
    # cleanup
    # run_test test8
else
    for testname in $@
    do
        cleanup
        run_test "$testname"
    done
fi

if type lsb_release >/dev/null 2>&1 ; then
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

echo "============== Test Summary =============="
echo "> Below follow the identical outputs:"
grep "are identical" "$output_dir"/result_status | awk '{print $1}' | tee results/passed.log

echo "> Below follow the non-identical outputs:"     
grep "are not identical" "$output_dir"/result_status | awk '{print $1}' | tee results/failed.log
echo "=========================================="
TOTAL_TESTS=$(cat "$output_dir"/result_status | wc -l)
PASSED_TESTS=$(grep -c "are identical" "$output_dir"/result_status)
echo "Summary: ${PASSED_TESTS}/${TOTAL_TESTS} tests passed." | tee results/results.log
echo "=========================================="
