for test in $(cat all_benchmarks); do
    echo "Running $test..."
    ./benchmarks/${test}/run --target both
done