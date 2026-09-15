#!/bin/sh
# Download many URLs concurrently into one directory.
#
#   fetch_parallel.sh DIR [JOBS] < urls     (one URL per line; default 16 jobs)
#
# Each file is saved under its basename in DIR, resumed if partially present,
# and retried on stalls. Exists because several benchmark setups fetch dozens
# to hundreds of small files one at a time: the per-request round trip, not
# bandwidth, is what makes those slow, so running the requests concurrently
# is the fix. (For a single huge file from a per-connection-throttled host,
# see bio4's setup, which splits one file across connections instead.)
#
# xargs -P is a GNU/BSD extension, but every image here is Debian.
dir=$1
jobs=${2:-16}
if [ -z "$dir" ]; then
    echo "usage: fetch_parallel.sh DIR [JOBS] < urls" >&2
    exit 2
fi
mkdir -p "$dir"
xargs -P "$jobs" -n 1 wget -q -c --timeout=60 --tries=5 --waitretry=5 -P "$dir"
