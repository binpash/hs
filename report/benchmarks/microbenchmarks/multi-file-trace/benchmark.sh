#!/bin/bash
mkdir -p "$output_dir" "$output_dir/1" "$output_dir/2" "$output_dir/3" "$output_dir/4" "$output_dir/5" "$output_dir/6" "$output_dir/7" "$output_dir/8" 

"$SOURCE_DIR/create-files-loop.sh" "$output_dir/1" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/2" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/3" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/4" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/5" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/6" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/7" $count $size
"$SOURCE_DIR/create-files-loop.sh" "$output_dir/8" $count $size