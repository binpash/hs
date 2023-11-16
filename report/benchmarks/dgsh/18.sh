#!/bin/sh

# Adapted from: dspinellis/dgsh
# Source file example/dir.sh
#!/usr/bin/env pa.sh
#
# SYNOPSIS Directory listing
# DESCRIPTION
# Windows-like DIR command for the current directory.
# Modified to use intermediate files instead of command substitution.
#
#  Copyright 2012-2013 Diomidis Spinellis
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# Create temporary files
free_space_file=$(mktemp)
file_details_file=$(mktemp)
file_count_file=$(mktemp)
dir_count_file=$(mktemp)
byte_count_file=$(mktemp)

# Get free space
df -h . | awk '!/Use%/{print $4}' > "$free_space_file"

# List details of files and directories
ls -l | awk '!/^total/ {print $6, $7, $8, $1, sprintf("%8d", $5), $9}' > "$file_details_file"

# Count number of files
ls -l | grep -v '^total' | grep -v '^d' | wc -l > "$file_count_file"

# Count number of directories
ls -l | grep '^d' | wc -l > "$dir_count_file"

# Calculate total bytes
ls -l | awk '{if($1 != "total") s += $5} END {print s}' > "$byte_count_file"

# Display the results
cat "$file_details_file"
echo "               $(cat "$file_count_file") File(s) $(cat "$byte_count_file") bytes"
echo "               $(cat "$dir_count_file") Dir(s) $(cat "$free_space_file") bytes free"

# Clean up temporary files
rm -f "$free_space_file" "$file_details_file" "$file_count_file" "$dir_count_file" "$byte_count_file"
