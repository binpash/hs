#!/bin/bash
# Build articles100m1m (every article of articles100m inflated to 1 MB), the
# input of web-index-100m1m. Built into a temporary name and renamed at the
# end, so an interrupted setup reruns it instead of leaving a partial tree.
# (A 500K variant used to be built too; no benchmark size reads it.)
set -e
BENCH_TOP=${BENCH_TOP:-$(git rev-parse --show-toplevel)}
RESOURCE_DIR=${RESOURCES_DIR:-$BENCH_TOP/report/resources/web-index}

src="$RESOURCE_DIR/articles100m" dst="$RESOURCE_DIR/articles100m1m"
if [ -d "$dst" ]; then
    echo "$dst already built, skipping"
    exit 0
fi
rm -rf "$dst.partial"
python3 "$BENCH_TOP/report/util/inflate_tree.py" "$src" "$dst.partial" 1M --glob '*.html'
mv "$dst.partial" "$dst"
