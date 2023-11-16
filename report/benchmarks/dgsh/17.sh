#!/bin/bash

# Adapted from: dspinellis/dgsh
# Source file example/reorder-columns.sh
# SYNOPSIS Reorder columns
# DESCRIPTION
# Reorder columns in a CSV document.
# Demonstrates the combined use of tee, cut, and paste.
#
#
# Recommended inputs:
# 5GB:   https://testfile.org/files-5GB
# 1GB:   https://bit.ly/1GB-testfile
# 700MB: http://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/pir/psd7003.xml
# 120MB: http://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/dblp/dblp.xml
# 23MB:  http://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/nasa/nasa.xml
# 2MB:   http://aiweb.cs.washington.edu/research/projects/xmltk/xmldata/data/courses/uwm.xml
#
#
#  Copyright 2016 Marios Fragkoulis
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

# Initialize the necessary temporary files
file1=$(mktemp)
file2=$(mktemp)
file3=$(mktemp)
file4=$(mktemp)

# Save the ls output to a temporary file
ls -n > "$file1"

# Reorder fields in DIR-like way
awk '!/^total/ {print $6, $7, $8, $1, sprintf("%8d", $5), $9}' "$file1" > "$file2"

# Count number of files
wc -l "$file1" | tr -d \\n > "$file3"
echo -n ' File(s) ' >> "$file3"
awk '{s += $5} END {printf("%d bytes\n", s)}' "$file1" >> "$file3"

# Count number of directories and print label for number of dirs and calculate free bytes
grep -c '^d' "$file1" | tr -d \\n > "$file4"
df -h . | awk '!/Use%/{print " Dir(s) " $4 " bytes free"}' >> "$file4"

# Display the results
cat "$file2" "$file3" "$file4"
