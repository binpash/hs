#!/bin/bash

#set -e

# Setting environment variables
export PATH=$PATH:$HOME/.local/bin
export PASH_SPEC_TOP=${PASH_SPEC_TOP:-$(git rev-parse --show-toplevel --show-superproject-working-tree)}
export PASH_TOP=${PASH_TOP:-$PASH_SPEC_TOP/deps/pash}

# Directory configurations
resource_dir="$PASH_SPEC_TOP/report/resources"
download_dir="$resource_dir/unix50"
mkdir -p "$download_dir"
cd "$download_dir"

# Define inputs
inputs=(
1 10 11 12 2 3 4 5 6 7 8 9.1 9.2 9.3 9.4 9.5 9.6 9.7 9.8 9.9
)

# Function to append newline if not present
append_nl_if_not() {
    if [ -z "$1" ]; then
        echo "No file argument given!"
        exit 1
    elif [ ! -f "$1" ]; then
        echo "File $1 doesn't exist!"
        exit 1
    else
        tail -c 1 "$1" | od -ta | grep -q nl || echo >> "$1"
    fi
}

# Function to setup the dataset
setup_dataset() {
    for input in ${inputs[@]}; do
        append_nl_if_not "${input}.txt"
    done
}

# Function to handle argument variables
source_var() {
    if [[ $small_flag -eq 1 ]]; then
        export IN_PRE=$PASH_TOP/evaluation/benchmarks/unix50/input/small
    else
        export IN_PRE=$PASH_TOP/evaluation/benchmarks/unix50/input
    fi
}

download_data() {
    echo "Downloading and unzipping data..."
    # TODO: add Omega URL when available
    # wget -O unix50.zip https://atlas-group.cs.brown.edu/data/ && unzip unix50.zip && rm -rf unix50.zip
}

# Parse arguments
small_flag=0
full_flag=0
gen_full_flag=0
download_flag=0
while getopts ":sfgd" opt; do
  case $opt in
    s) small_flag=1 ;;
    f) full_flag=1 ;;
    g) gen_full_flag=1 ;;
    d) download_flag=1 ;;
    \?) echo "Invalid option -$OPTARG" >&2 ;;
  esac
done

# Conditional executions based on flags
[[ $download_flag -eq 1 ]] && download_data
[[ $small_flag -eq 1 ]] && setup_dataset --small
[[ $full_flag -eq 1 ]] || [[ $gen_full_flag -eq 1 ]] && setup_dataset
source_var

# Function to create larger input files if --full or --gen-full flag is set
generate_larger_inputs() {
    if [[ $full_flag -eq 1 ]]; then
        for file in *.txt; do
            echo '' > temp.txt
            for (( i = 0; i < 100; i++ )); do
                cat $file >> temp.txt
            done
            mv temp.txt $file
        done
    fi

    if [[ $gen_full_flag -eq 1 ]]; then
        echo "Generating full-size inputs"

        for file in *.txt; do
            new_file=$(basename $file .txt).1G.txt
            max=$(echo "1000000000 / $(stat --printf="%s" $file)" | bc)
            echo "Generating 1-G $new_file (${max}x increase)"
            for (( i = 0; i < max ; i++ )); do
                cat $file >> $new_file
            done
        done
    fi
}

# Function to clean up the directory
cleanup() {
    echo "Cleaning up temporary files..."
    rm -f temp.txt
}

# Call the functions based on the flags
generate_larger_inputs
cleanup

# Final message
echo "Benchmark input setup is complete."
