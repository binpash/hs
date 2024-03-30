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

# Check if correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input_file> <target_size>"
    echo "Example: $0 input.txt 5M"
    exit 1
fi

input_file="$1"
target_size="$2"

# Check if input file exists
if [ ! -f "$input_file" ]; then
    echo "Error: Input file '$input_file' not found."
    exit 1
fi

# Get the size of the input file
input_size=$(stat -c%s "$input_file")

# Convert target size to bytes
target_size_bytes=$(convert_to_bytes "$target_size")

# Check if target size is smaller than input file size
if [ "$target_size_bytes" -le "$input_size" ]; then
    echo "Error: Target size must be greater than the size of the input file."
    exit 1
fi

# Calculate the number of times to repeat the file
repeats=$(( ($target_size_bytes + $input_size - 1) / $input_size ))

# Create a temporary file to store repeated contents
temp_file=$(mktemp)

# Repeat the contents of the input file
for (( i=0; i<$repeats; i++ )); do
    cat "$input_file" >> "$temp_file"
done

# Trim the temporary file to the target size
truncate -s "$target_size_bytes" "$temp_file"

# Rename the temporary file to the original file name
mv "$temp_file" "$target_size-$input_file"

# Calculate percentage of inflation
percentage_inflation=$(( (($target_size_bytes - $input_size) * 100) / $input_size ))

# Calculate how many times larger the inflated file got
times_larger=$(( $target_size_bytes / $input_size ))

echo "$input_file inflated successfully to $target_size ($percentage_inflation% inflation, $times_larger times larger)."
