#!/bin/bash
# bulkrename--Renames specified files by replacing text in the filename

printHelp() {
    echo "Usage: $0 -f find -r replace FILES_TO_RENAME*"
    echo -e "\t-f The text to find in the filename"
    echo -e "\t-r The replacement text for the new filename"
    exit 1
}

while getopts "f:r:" opt; do
    case "$opt" in
        r)
            replace="$OPTARG"
            ;;
        f)
            match="$OPTARG"
            ;;
        ?)
            printHelp
            ;;
    esac
done

shift $(( $OPTIND - 1 ))

if [ -z $replace ] || [ -z $match ]; then
    echo "You need to supply a string to find and a string to replace"
    printHelp
fi

for i in "$@"; do
    newname=$(echo $i | sed "s/$match/$replace/")
    mv $i $newname && echo "Renamed file $i to $newname"
done