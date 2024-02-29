if [ ! -f bus.csv ]; then
    echo "Downloading full-size dataset..."
    wget -nc -O bus.csv.bz2 'https://www.balab.aueb.gr/~dds/oasa-2021-01-08.bz2'
    if [[ -f bus.csv.bz2 ]]; then
        echo "Decompressing full-size dataset..."
        bzip2 -d bus.csv.bz2
    fi
else
    echo "Full-size dataset already exists."
fi
