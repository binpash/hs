#!/usr/bin/env python3
"""Mirror a directory tree, inflating every matching file to a fixed size.

    inflate_tree.py SRC DST SIZE [--glob '*.html'] [--jobs N]

Each matching file under SRC is written to the same relative path under DST,
its content repeated (the same doubling inflate.py does) until it is exactly
SIZE bytes; SIZE takes K/M/G suffixes. Files already at least SIZE are copied
as they are. Other files are copied unchanged. One process per core instead
of one interpreter per file, and one summary line instead of one per file.
"""
import argparse
import fnmatch
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

UNITS = {"K": 1 << 10, "M": 1 << 20, "G": 1 << 30}


def to_bytes(size):
    unit = size[-1].upper()
    return int(size[:-1]) * UNITS[unit] if unit in UNITS else int(size)


def inflated(content, target):
    """Same bytes inflate.py produces: double while it fits, then top up."""
    if not content or len(content) >= target:
        return content
    while len(content) * 2 <= target:
        content += content
    return content + content[:target - len(content)]


def work(job):
    src, dst, target = job
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if target is None:
        shutil.copyfile(src, dst)
        return 0
    with open(src, "rb") as f:
        data = inflated(f.read(), target)
    with open(dst, "wb") as f:
        f.write(data)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("size")
    ap.add_argument("--glob", default="*.html")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    a = ap.parse_args()

    target = to_bytes(a.size)
    jobs = []
    for root, _, files in os.walk(a.src):
        rel = os.path.relpath(root, a.src)
        for name in files:
            match = fnmatch.fnmatch(name, a.glob)
            jobs.append((os.path.join(root, name),
                         os.path.normpath(os.path.join(a.dst, rel, name)),
                         target if match else None))

    with ProcessPoolExecutor(a.jobs) as pool:
        n = sum(pool.map(work, jobs, chunksize=64))
    print(f"inflated {n} files to {a.size} ({len(jobs) - n} copied as-is): {a.src} -> {a.dst}")


if __name__ == "__main__":
    sys.exit(main())
