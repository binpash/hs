#!/usr/bin/env python3
"""Process benchmark results and validate output correctness."""

import argparse
import filecmp
import json
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate results/processed.json")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("results/"),
        help="Results directory",
    )
    parser.add_argument(
        "-n",
        "--no-check",
        dest="check",
        action="store_false",
        help="Skip correctness check",
    )
    return parser.parse_args()


class OutputComparison(NamedTuple):
    names_match: bool
    contents_match: bool


def check_output_correctness(benchmark: str) -> OutputComparison:
    """Check if spec and sub output match for a benchmark.

    Args:
        benchmark: Benchmark name (e.g., 'bioinfo-automine')

    Returns:
        OutputComparison tuple of (names_match, contents_match)
    """
    spec_output = Path(f"output/spec-{benchmark}")
    sub_output = Path(f"output/sub-{benchmark}")

    if not spec_output.exists() or not sub_output.exists():
        print(f"Warning: Missing output directories for {benchmark}", file=sys.stderr)
        return OutputComparison(False, False)

    comparison = filecmp.dircmp(spec_output, sub_output)

    def check_names(dcmp: filecmp.dircmp) -> bool:
        if dcmp.left_only or dcmp.right_only:
            return False
        return all(check_names(sub) for sub in dcmp.subdirs.values())

    def is_video_file(path: Path) -> bool:
        return path.suffix.lower() in {".mkv", ".mp4", ".avi", ".mov", ".webm"}

    def videos_match(file1: Path, file2: Path) -> bool:
        """Check if two video files are visually identical."""
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(file1),
                "-i",
                str(file2),
                "-filter_complex",
                "[0:v][1:v]psnr=stats_file=-",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
        )
        # PSNR=inf means pixel-perfect match
        return "inf" in result.stdout.lower()

    def check_contents(dcmp: filecmp.dircmp) -> bool:
        # Check regular files that differ
        for name in dcmp.diff_files:
            left_path = Path(dcmp.left) / name
            right_path = Path(dcmp.right) / name

            # If both are video files, use visual comparison
            if is_video_file(left_path) and is_video_file(right_path):
                if not videos_match(left_path, right_path):
                    return False
            else:
                # Non-video files must match exactly
                return False

        if dcmp.funny_files:
            return False

        return all(check_contents(sub) for sub in dcmp.subdirs.values())

    return OutputComparison(check_names(comparison), check_contents(comparison))


def parse_hyperfine_json(filepath: Path) -> float | None:
    """Extract mean runtime from hyperfine JSON output.

    Args:
        filepath: Path to hyperfine JSON file

    Returns:
        Mean runtime in seconds
    """
    with open(filepath) as f:
        try:
            data: dict[str, Any] = json.load(f)
        except json.JSONDecodeError:
            return None

    assert len(data["results"]) == 1
    return float(data["results"][0]["mean"])


def get_stats(data: list[dict[str, Any]], version: str) -> dict[str, Any]:
    """Get statistics for a specific version (sub or multi)."""
    mean_key = f"{version}_mean"
    speedup_key = f"{version}_speedup"
    filtered = [v for v in data if mean_key in v and v[mean_key] is not None]
    if not filtered:
        return {}
    return {
        f"{version}_geomean_speedup": statistics.geometric_mean(
            v[speedup_key] for v in filtered
        ),
        f"min_spec_time_{version}": min(v["spec_mean"] for v in filtered),
        f"max_spec_time_{version}": max(v["spec_mean"] for v in filtered),
        f"min_{version}_time": min(v[mean_key] for v in filtered),
        f"max_{version}_time": max(v[mean_key] for v in filtered),
        f"min_{version}_speedup": min(v[speedup_key] for v in filtered),
        f"max_{version}_speedup": max(v[speedup_key] for v in filtered),
    }


def main() -> int:
    args = parse_args()
    check = args.check
    results_dir: Path = parse_args().input

    # Find all benchmark names by looking at spec-*.json files (spec is required)
    spec_files = list(results_dir.glob("spec-*.json"))
    processed_data = []

    for spec_file in spec_files:
        # Extract benchmark name from filename (e.g., spec-bioinfo-automine.json)
        benchmark = spec_file.stem.replace("spec-", "")
        sub_file = results_dir / f"sub-{benchmark}.json"
        multi_file = results_dir / f"multi-{benchmark}.json"
        bad_spec_file = results_dir / f"bad_spec-{benchmark}.json"

        # Parse timing data
        spec_mean = parse_hyperfine_json(spec_file)
        if spec_mean is None:
            print(f"Warning: Invalid spec results for {benchmark}", file=sys.stderr)
            continue

        sub_mean = parse_hyperfine_json(sub_file) if sub_file.exists() else None
        multi_mean = parse_hyperfine_json(multi_file) if multi_file.exists() else None
        bad_mean = parse_hyperfine_json(bad_spec_file) if multi_file.exists() else None

        if sub_mean is None:
            print(f"Warning: Missing sub results for {benchmark}", file=sys.stderr)
            continue

        names_match, contents_match = (
            check_output_correctness(benchmark) if check else (False, False)
        )

        entry = {
            "benchmark": benchmark,
            "sub_mean": sub_mean,
            "spec_mean": spec_mean,
            "names_match": names_match,
            "contents_match": contents_match,
            "spec_speedup_compared_with_sub": sub_mean / spec_mean,
        }

        if multi_mean is not None:
            entry["multi_mean"] = multi_mean
            entry["spec_slowdown_compared_with_multi"] = multi_mean / spec_mean

        if bad_mean is not None:
            entry["bad_mean"] = bad_mean
            entry["bad_slowdown_compared_with_sub"] = bead_mean / sub_mean

        processed_data.append(entry)

    # Get statistics for each version separately
    stats = {}
    stats.update(get_stats(processed_data, "sub"))
    stats.update(get_stats(processed_data, "multi"))
    stats["data"] = processed_data

    # Write processed results
    output_file = results_dir / "processed.json"
    with open(output_file, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Processed {len(processed_data)} benchmarks -> {output_file}")

    failed = False

    for item in processed_data:
        if not item["contents_match"]:
            print(f"\nWARNING: {item['benchmark']} failed contents correctness check:")
            if item["names_match"]:
                print(f"GOOD: {item['benchmark']} passed file name correctness check")
            else:
                print(
                    f"ERROR: {item['benchmark']} also failed file name correctness check"
                )
                failed = True
        else:
            print(f"\nVERY GOOD: {item['benchmark']} passed contents correctness check")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
