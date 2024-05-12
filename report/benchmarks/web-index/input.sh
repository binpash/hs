
wiki_archive="https://dumps.wikimedia.org/other/static_html_dumps/current/en/wikipedia-en-html.tar.7z"
BENCH_TOP=${BENCH_TOP:-$(git rev-parse --show-toplevel)}
RESOURCES_DIR=${RESOURCES_DIR:-$BENCH_TOP/report/resources/web-index/}

mkdir -p $RESOURCES_DIR

if [[ ! -d "$RESOURCES_DIR/en" ]]; then
  if [ "$1" = "--small" ]; then
    # 500 entries
    wget -0 $RESOURCES_DIR/wikipedia500.tar.gz https://atlas-group.cs.brown.edu/data/web-index/wikipedia500.tar.gz 
    wget -0 $RESOURCES_DIR/index500.txt https://atlas-group.cs.brown.edu/data/web-index/index500.txt 
    tar -xf $RESOURCES_DIR/wikipedia500.tar.gz -C $RESOURCES_DIR
  elif [ "$1" = "--meduim" ]; then
    the default full
    # 1000 entries
    wget https://atlas-group.cs.brown.edu/data/web-index/wikipedia1000.tar.gz -0 $RESOURCES_DIR/wikipedia1000.tar.gz
    wget https://atlas-group.cs.brown.edu/data/web-index/index1000.txt -0 $RESOURCES_DIR/index1000.txt
    tar -xf $RESOURCES_DIR/wikipedia1000.tar.gz -C $RESOURCES_DIR
  else
    # full dataset
    echo "Downloading the full dataset. Caution!! file around 210GB"
    wget -O wikipedia-en-html.tar.7z $wiki_archive
    7z x wikipedia-en-html.tar.7z
    tar -xvf wikipedia-en-html.tar -C $RESOURCES_DIR
  fi
fi