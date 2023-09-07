#!/bin/bash

# Consistent sorting across machines
# export LC_ALL=C

# Temporary files
file1=$(mktemp)
file2=$(mktemp)
file3=$(mktemp)
file4=$(mktemp)

cat $INPUT_FILE > $file1
cat $file1

# Split input one word per line
tr -cs a-zA-Z '\n' < "$file1" > "$file2"

# Digram frequency
echo "Digram frequency"
perl -ne 'for ($i = 0; $i < length($_) - 2; $i++) {
	print substr($_, $i, 2), "\n";
}' < "$file2" |
awk '{count[$1]++} END {for (i in count) print count[i], i}' |
sort -rn

# Trigram frequency
echo "Trigram frequency"
perl -ne 'for ($i = 0; $i < length($_) - 3; $i++) {
	print substr($_, $i, 3), "\n";
}' < "$file2" |
awk '{count[$1]++} END {for (i in count) print count[i], i}' |
sort -rn

# Word frequency
echo "Word frequency"
awk '{count[$1]++} END {for (i in count) print count[i], i}' < "$file2" |
sort -rn

# Store number of characters to use in awk below

nchars=$(wc -c < "$file1")

# Character frequency
# Print absolute
echo "Character frequency"
sed 's/./&\n/g' < "$file1" |
awk '{count[$1]++} END {for (i in count) print count[i], i}' |
sort -rn | tee "$file3"

# Print relative
# echo "Relative character frequency"
# awk -v NCHARS=$nchars 'BEGIN {
# 		OFMT = "%.2g%%"}
# 		{print $1, $2, $1 / NCHARS * 100}' "$file3"