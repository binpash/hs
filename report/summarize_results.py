#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


FIELDNAMES = [
    "benchmark",
    "test",
    "window",
    "target",
    "sh_time_s",
    "hs_time_s",
    "speedup_sh_over_hs",
    "relative_speedup_pct",
    "timestamp_utc",
    "args",
    "output_dir",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Aggregate hS benchmark outputs.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="Directory containing benchmark output subdirectories.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "output" / "results_summary.csv",
        help="CSV path to write.",
    )
    return parser.parse_args()


def read_float(path):
    if not path.exists():
        return None
    try:
        return float(path.read_text().strip())
    except ValueError:
        return None


def read_metadata(output_dir):
    metadata = {}
    metadata_path = output_dir / "run_metadata.env"
    if not metadata_path.exists():
        return metadata

    for line in metadata_path.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        metadata[key] = value
    return metadata


def discover_output_dirs(output_dir):
    dirs = set()
    for name in ("sh_time", "hs_time"):
        for path in output_dir.rglob(name):
            dirs.add(path.parent)
    return sorted(dirs, key=lambda path: path.relative_to(output_dir).as_posix())


def make_row(base_output_dir, output_dir):
    rel = output_dir.relative_to(base_output_dir)
    rel_parts = rel.parts
    benchmark = rel_parts[0] if rel_parts else output_dir.name
    test = rel.as_posix()

    metadata = read_metadata(output_dir)
    benchmark = metadata.get("benchmark", benchmark)
    test = metadata.get("test", test)

    sh_time = read_float(output_dir / "sh_time")
    hs_time = read_float(output_dir / "hs_time")
    speedup = None
    relative_speedup = None
    if sh_time is not None and hs_time not in (None, 0):
        speedup = sh_time / hs_time
        relative_speedup = (speedup - 1.0) * 100.0

    return {
        "benchmark": benchmark,
        "test": test,
        "window": metadata.get("window", ""),
        "target": metadata.get("target", ""),
        "sh_time_s": "" if sh_time is None else f"{sh_time:.6f}",
        "hs_time_s": "" if hs_time is None else f"{hs_time:.6f}",
        "speedup_sh_over_hs": "" if speedup is None else f"{speedup:.6f}",
        "relative_speedup_pct": ""
        if relative_speedup is None
        else f"{relative_speedup:.2f}",
        "timestamp_utc": metadata.get("timestamp_utc", ""),
        "args": metadata.get("args", ""),
        "output_dir": output_dir.as_posix(),
    }


def main():
    args = parse_args()
    output_dir = args.output_dir.resolve()
    rows = [make_row(output_dir, path) for path in discover_output_dirs(output_dir)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {args.output} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
