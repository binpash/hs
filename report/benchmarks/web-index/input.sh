#!/bin/bash

BENCH_TOP=${BENCH_TOP:-$(git rev-parse --show-toplevel)}
RESOURCES_DIR=${RESOURCES_DIR:-$BENCH_TOP/report/resources/web-index/}

mkdir -p $RESOURCES_DIR

if [[ ! -d "$RESOURCES_DIR/en" ]]; then
  if [ "$1" = "--small" ]; then
    # 1000 entries
    wget -O $RESOURCES_DIR/wikipedia-small.tar.gz https://atlas-group.cs.brown.edu/data/wikipedia/input_small/articles.tar.gz
    wget -O $RESOURCES_DIR/index_small.txt https://atlas-group.cs.brown.edu/data/wikipedia/input_small/index.txt 
    tar -xf $RESOURCES_DIR/wikipedia-small.tar.gz -C $RESOURCES_DIR
  else
    # full dataset
    echo "Downloading the full dataset. Caution!! file around 210GB"
    wget -O $RESOURCES_DIR/wikipedia.tar.gz https://atlas-group.cs.brown.edu/data/wikipedia/input/articles.tar.gz
    wget -O $RESOURCES_DIR/index.txt https://atlas-group.cs.brown.edu/data/wikipedia/input/index.txt
    tar -xf $RESOURCES_DIR/wikipedia.tar.gz -C $RESOURCES_DIR
  fi
fi
