#!/bin/bash

cd "$(realpath $(dirname "$0"))"
mkdir -p inputs
cd inputs

if [ ! -f ./book_links.txt ]; then
    wget --no-check-certificate -O book_links.txt "https://atlas.cs.brown.edu/data/gutenberg/books.txt"
    if [ ! -f book_links.txt ]; then
        echo "Failed to download book_links.txt"
        exit 1
    fi
fi

if [ ! -f ./genesis ]; then
    wget --no-check-certificate -O genesis "https://atlas.cs.brown.edu/data/gutenberg/8/0/0/8001/8001.txt"
fi 

if [ ! -f ./exodus ]; then
    wget --no-check-certificate -O exodus "https://atlas.cs.brown.edu/data/gutenberg/3/3/4/2/33420/33420-0.txt"
fi

if [ ! -e ./pg ]; then
    mkdir pg
    cd pg
    book_count=120

    head -n $book_count ../book_links.txt | while IFS= read -r line
    do
        full_url="https://atlas.cs.brown.edu/data/gutenberg/${line}"
        echo "Downloading $full_url"
        wget --no-check-certificate -q "$full_url"
    done

    cd ..
fi

if [ ! -e ./pg-small ]; then
    mkdir pg-small
    cd pg-small
    book_count=10

    head -n $book_count ../book_links.txt | while IFS= read -r line
    do
        full_url="https://atlas.cs.brown.edu/data/gutenberg/${line}"
        echo "Downloading $full_url"
        wget --no-check-certificate -q "$full_url"
    done

    cd ..
fi
