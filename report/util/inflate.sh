#!/bin/bash

# Function to convert size to bytes
convert_to_bytes() {
    local size_str="$1"
    local size_unit="${size_str: -1}"
    local size_value="${size_str:0: -1}"
    local bytes=0

    case "$size_unit" in
        "K") bytes=$((size_value * 1024));;
        "M") bytes=$((size_value * 1024 * 1024));;
        "G") bytes=$((size_value * 1024 * 1024 * 1024));;
        *)   bytes="$size_str";;
    esac

    echo "$bytes"
}

# Check if at least two arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_file> <target_size_1> [<target_size_2> ...]"
    echo "Example: $0 input.txt 5M 10M 1G"
    exit 1
fi

input_file="$1"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' not found."
    exit 1
fi

# Get the size of the input file
input_size=$(stat -c%s "$input_file")

# Iterate over each target size argument
shift # Skip the first argument, which is the input file name
for target_size in "$@"; do

    # Convert target size to bytes
    target_size_bytes=$(convert_to_bytes "$target_size")

    # Check if target size is smaller than input file size
    if [ "$target_size_bytes" -le "$input_size" ]; then
        echo "Error: Target size $target_size must be greater than the size of the input file."
        echo "Setting target size to the size of the input file."
        target_size_bytes=$input_size
    fi

    # Define output file name
    output_file="$target_size-$input_file"
    cp "$input_file" "$output_file"

    # Use file doubling to efficiently reach the target size
    current_size=$input_size
    while [ $((current_size * 2)) -le "$target_size_bytes" ]; do
        # Use a temporary file to avoid "input file is output file" error
        temp_file=$(mktemp)
        cat "$output_file" "$output_file" > "$temp_file"
        mv "$temp_file" "$output_file"
        current_size=$((current_size * 2))
    done

    # Final adjustments to reach the exact target size
    while [ $current_size -lt "$target_size_bytes" ]; do
        # Calculate remaining bytes to reach target size
        remaining=$((target_size_bytes - current_size))
        if [ $remaining -gt $input_size ]; then
            cat "$input_file" >> "$output_file"
            current_size=$((current_size + input_size))
        else
            # Use dd with seek to append the final bytes without overwriting
            dd if="$input_file" of="$output_file" bs=1 count="$remaining" seek="$current_size" conv=notrunc
            break
        fi
    done

    echo "$input_file inflated successfully to $target_size."
done
