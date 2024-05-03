#!/bin/bash
# showfile--Shows the contents of a file, including additional useful info

# 29 Displaying a File with Additional Information

width=72
for input
do
    lines="$(wc -l < $input | sed 's/ //g')"
    chars="$(wc -c < $input | sed 's/ //g')"
    owner="$(ls -ld $input | awk '{print $3}')"
    102 Chapter 4
    echo "-----------------------------------------------------------------"
    echo "File $input ($lines lines, $chars characters, owned by $owner):"
    echo "-----------------------------------------------------------------"
    while read line
    do
    if [ ${#line} -gt $width ] ; then
        echo "$line" | fmt | sed -e '1s/^/ /' -e '2,$s/^/+ /'
    else
        echo " $line"
    fi
    done < $input
    echo "-----------------------------------------------------------------"
done | ${PAGER:more}
