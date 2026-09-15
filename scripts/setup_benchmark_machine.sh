#!/bin/bash
#
# One-time preparation of a fresh benchmark machine (CloudLab nodes in mind,
# any Debian/Ubuntu box works). Run it once as the user who will run the
# benchmarks; every step is idempotent, so re-running is harmless.
#
#   scripts/setup_benchmark_machine.sh [-y] [--disk DEV|MOUNTPOINT] [--min-gb N]
#
# It does the things a node needs before ./setup and ./run in report/benchmarks
# can work, and that would otherwise be repeated by hand on every node:
#
#   1. Install docker (official packages) and let this user run it.
#   2. Pick the disk that everything benchmark-related lives on. CloudLab's
#      root partition is ~16 GB whatever the physical disk, and the big disk
#      (/mydata, or a blank extra drive) differs per node type: SSD on most
#      Utah types, spinning on many Wisconsin/Clemson ones with the SSD left
#      unmounted. So: consider every mounted filesystem and every blank,
#      unmounted disk; prefer a non-rotational one with at least --min-gb
#      (default 200) free, else the largest; format and mount a blank disk
#      if that is the winner. --disk overrides the choice.
#   3. Create the hs data directory on it, <disk>/hs, holding
#        resources/  benchmark inputs (downloaded by each suite's ./setup)
#        tmp/        the container's /tmp: hs scratch, max_temp's overlay upper
#        docker/     docker's data-root: images and container layers, which is
#                    where report/output is written before being copied out
#      and record it in ~/.config/hs/data_dir, which report/setup_base and
#      report/run_base read (HS_DATA in the environment overrides it).
#   4. Point docker's data-root there (/etc/docker/daemon.json), unless the
#      daemon already has one configured, and restart it.
#   5. If this checkout's report/resources already holds inputs, move them
#      into the data directory and leave a symlink behind, so --local runs
#      (which use report/resources directly) see the same files.
#
# --local runs additionally need scripts/install_deps_ubuntu20.sh.
set -eu

YES=0
DISK=""
MIN_GB=200
while [ $# -gt 0 ]; do
    case "$1" in
        -y|--yes) YES=1 ;;
        --disk) shift; DISK=$1 ;;
        --min-gb) shift; MIN_GB=$1 ;;
        -h|--help) sed -n '3,/^set -eu/p' "$0" | sed '$d' | cut -c3-; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
    shift
done

repo_root=$(cd "$(dirname "$(realpath -se "$0")")/.." && pwd)
me=$(id -un)
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/hs"

confirm() {
    [ "$YES" -eq 1 ] && return 0
    printf '%s [y/N] ' "$1"
    read -r answer
    case "$answer" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# ---------------------------------------------------------------------------
echo "== 1. docker"
if command -v docker >/dev/null 2>&1; then
    echo "   already installed: $(docker --version)"
else
    echo "   installing docker from the official repository"
    curl -fsSL https://get.docker.com | sudo sh
fi
sudo systemctl enable --now docker >/dev/null
if id -nG "$me" | tr ' ' '\n' | grep -qx docker; then
    echo "   $me is already in the docker group"
else
    sudo usermod -aG docker "$me"
    echo "   added $me to the docker group (takes effect on next login; 'newgrp docker' for this shell)"
fi

# ---------------------------------------------------------------------------
echo "== 2. data disk"
# One candidate per line: "<kind> <ssd 0/1> <free bytes> <device> <mountpoint>"
#   fs     a mounted filesystem (free = df available)
#   blank  an unmounted whole disk with no filesystem and no partitions
#          (free = its size)
candidates() {
    # lsblk -P prints KEY="value" pairs; prefix them before eval so the PATH
    # column cannot clobber $PATH.
    lsblk -b -n -P -o PATH,TYPE,SIZE,ROTA,MOUNTPOINT,FSTYPE | sed 's/\([A-Z]*\)=/lb_\1=/g' | while IFS= read -r line; do
        eval "$line"
        ssd=$((1 - lb_ROTA))
        if [ "$lb_TYPE" = disk ] && [ -z "$lb_FSTYPE" ] && [ -z "$lb_MOUNTPOINT" ] \
            && [ "$(lsblk -n -o NAME "$lb_PATH" | wc -l)" -eq 1 ]; then
            echo "blank $ssd $lb_SIZE $lb_PATH -"
        fi
        case "$lb_MOUNTPOINT" in
            ""|/boot|/boot/*|"[SWAP]"|/snap/*) continue ;;
        esac
        case "$lb_FSTYPE" in nfs*|tmpfs|squashfs|overlay|iso9660|vfat) continue ;; esac
        free=$(df -B1 --output=avail "$lb_MOUNTPOINT" | tail -1 | tr -d ' ')
        echo "fs $ssd $free $lb_PATH $lb_MOUNTPOINT"
    done
}

all=$(candidates)
echo "   candidates:"
echo "$all" | awk '{ printf "     %-5s %s %6.0f GB free  %s  %s\n", $1, ($2?"ssd":"hdd"), $3/1e9, $4, $5 }'

min_bytes=$((MIN_GB * 1000000000))
if [ -n "$DISK" ]; then
    choice=$(echo "$all" | awk -v d="$DISK" '$4 == d || $5 == d' | head -1)
    [ -n "$choice" ] || { echo "   --disk $DISK is neither a mounted filesystem nor a blank disk (see candidates)" >&2; exit 1; }
else
    # Biggest SSD with enough room, else the biggest anything.
    choice=$(echo "$all" | awk -v m="$min_bytes" '$2 == 1 && $3 >= m' | sort -k3 -n -r | head -1)
    [ -n "$choice" ] || choice=$(echo "$all" | sort -k3 -n -r | head -1)
fi
set -- $choice
kind=$1 ssd=$2 free=$3 dev=$4 mnt=$5
echo "   chosen: $dev ($([ "$ssd" = 1 ] && echo ssd || echo hdd), $((free / 1000000000)) GB free)"

if [ "$kind" = blank ]; then
    mnt=/hs-data
    echo "   $dev is a blank disk: it will be formatted ext4 and mounted at $mnt"
    confirm "   format $dev? (destroys anything on it)" || { echo "   aborted; use --disk to pick another"; exit 1; }
    sudo mkfs.ext4 -q -F "$dev"
    sudo mkdir -p "$mnt"
    sudo mount "$dev" "$mnt"
    uuid=$(sudo blkid -s UUID -o value "$dev")
    grep -q "UUID=$uuid" /etc/fstab || echo "UUID=$uuid $mnt ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab >/dev/null
fi
case "$mnt" in
    /) data_dir=/hs-data ;;
    *) data_dir=${mnt%/}/hs ;;
esac

# ---------------------------------------------------------------------------
echo "== 3. data directory $data_dir"
sudo mkdir -p "$data_dir/resources" "$data_dir/tmp" "$data_dir/docker"
sudo chown "$me:$(id -gn)" "$data_dir" "$data_dir/resources"
sudo chmod 1777 "$data_dir/tmp"
mkdir -p "$config_dir"
echo "$data_dir" > "$config_dir/data_dir"
echo "   recorded in $config_dir/data_dir"

# ---------------------------------------------------------------------------
echo "== 4. docker data-root"
configured=$(python3 -c 'import json
try: print(json.load(open("/etc/docker/daemon.json")).get("data-root", ""))
except Exception: print("")')
if [ -n "$configured" ]; then
    echo "   daemon.json already sets data-root=$configured; leaving it alone"
else
    echo "   setting data-root=$data_dir/docker"
    python3 - "$data_dir/docker" <<'PY' | sudo tee /etc/docker/daemon.json.new >/dev/null
import json, sys
try: cfg = json.load(open("/etc/docker/daemon.json"))
except Exception: cfg = {}
cfg["data-root"] = sys.argv[1]
print(json.dumps(cfg, indent=2))
PY
    sudo mv /etc/docker/daemon.json.new /etc/docker/daemon.json
    sudo systemctl restart docker
    echo "   docker restarted (images pulled or built before this are not carried over)"
fi

# ---------------------------------------------------------------------------
echo "== 5. this checkout's report/resources"
res="$repo_root/report/resources"
if [ -L "$res" ]; then
    echo "   already a symlink -> $(readlink "$res")"
elif [ -d "$res" ] && [ -n "$(ls -A "$res")" ]; then
    echo "   moving existing inputs into $data_dir/resources"
    for d in "$res"/*; do
        name=$(basename "$d")
        if [ -e "$data_dir/resources/$name" ]; then
            echo "   $name already exists in the data directory; leaving $d in place" >&2
        else
            mv "$d" "$data_dir/resources/"
        fi
    done
    if [ -z "$(ls -A "$res")" ]; then rmdir "$res" && ln -s "$data_dir/resources" "$res"; fi
else
    rm -rf "$res"
    ln -s "$data_dir/resources" "$res"
fi

echo
echo "done. Per suite:  cd report/benchmarks/<suite> && ./setup && ./<size>/run"
