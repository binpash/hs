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
# Progress is one line, "fetched N/M files", redrawn in place (a terminal) or
# printed every 10% (anything else); parallel per-file bars would interleave.
# A file that still fails after the retries is named, and the exit status is
# nonzero.
#
# xargs -P is a GNU/BSD extension, but every image here is Debian.
dir=$1
jobs=${2:-16}
if [ -z "$dir" ]; then
    echo "usage: fetch_parallel.sh DIR [JOBS] < urls" >&2
    exit 2
fi
mkdir -p "$dir"
urls=$(mktemp)
trap 'rm -f "$urls"' EXIT
cat > "$urls"
total=$(grep -c . "$urls")
tty=0; [ -t 1 ] && tty=1

grep . "$urls" \
    | xargs -P "$jobs" -n 1 sh -c \
        'if wget -q -c --timeout=60 --tries=5 --waitretry=5 -P "$0" "$1"; then echo ok; else echo "failed $1"; fi' "$dir" \
    | awk -v total="$total" -v tty="$tty" '
        $1 == "ok" { n++ }
        $1 == "failed" { bad++; printf "%sfailed: %s\n", (tty ? "\r\033[K" : ""), $2 > "/dev/stderr" }
        {
            done_ = n + bad
            if (tty) { printf "\r  fetched %d/%d files", n, total; fflush() }
            else if (done_ == total || int(done_ * 10 / total) > last) {
                last = int(done_ * 10 / total); printf "  fetched %d/%d files\n", n, total; fflush()
            }
        }
        END { if (tty) print ""; exit bad > 0 }'
