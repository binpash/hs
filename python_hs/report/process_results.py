#!/usr/bin/env python3
"""Process benchmark results and validate output correctness."""

import argparse
import filecmp
import json
import statistics
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate results/processed.json")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("results/"),
        help="Results directory",
    )
    return parser.parse_args()


def check_output_correctness(benchmark: str) -> bool:
    """Check if spec and sub output match for a benchmark.

    Args:
        benchmark: Benchmark name (e.g., 'bioinfo-automine')

    Returns:
        True if outputs match, False otherwise
    """
    spec_output = Path("output/spec-bench") / benchmark
    sub_output = Path("output/sub-bench") / benchmark

    if not spec_output.exists() or not sub_output.exists():
        print(f"Warning: Missing output directories for {benchmark}", file=sys.stderr)
        return False

    comparison = filecmp.dircmp(spec_output, sub_output)

    def check_dircmp(dcmp: filecmp.dircmp) -> bool:
        """Recursively check if directories are identical."""
        # Check for differences in files
        if dcmp.left_only or dcmp.right_only or dcmp.diff_files:
            return False

        # Check for differences in common files
        if dcmp.funny_files:
            return False

        # Recursively check subdirectories
        return all(check_dircmp(sub_dcmp) for sub_dcmp in dcmp.subdirs.values())

    is_correct = check_dircmp(comparison)

    if not is_correct:
        print(f"Mismatch detected in {benchmark} output", file=sys.stderr)

    return is_correct


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
    results_dir: Path = parse_args().input

    # Find all benchmark names by looking at spec-*.json files (spec is required)
    spec_files = list(results_dir.glob("spec-*.json"))
    processed_data = []

    for spec_file in spec_files:
        # Extract benchmark name from filename (e.g., spec-bioinfo-automine.json)
        benchmark = spec_file.stem.replace("spec-", "")
        sub_file = results_dir / f"sub-{benchmark}.json"
        multi_file = results_dir / f"multi-{benchmark}.json"

        # Parse timing data
        spec_mean = parse_hyperfine_json(spec_file)
        if spec_mean is None:
            print(f"Warning: Invalid spec results for {benchmark}", file=sys.stderr)
            continue

        sub_mean = parse_hyperfine_json(sub_file) if sub_file.exists() else None
        multi_mean = parse_hyperfine_json(multi_file) if multi_file.exists() else None

        if sub_mean is None:
            print(f"Warning: Missing sub results for {benchmark}", file=sys.stderr)
            continue

        # Check output correctness
        correct = check_output_correctness(benchmark)

        entry = {
            "benchmark": benchmark,
            "sub_mean": sub_mean,
            "spec_mean": spec_mean,
            "correct": correct,
            "sub_speedup": sub_mean / spec_mean,
        }

        if multi_mean is not None:
            entry["multi_mean"] = multi_mean
            entry["multi_speedup"] = multi_mean / spec_mean

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

    # Exit with error if any benchmark failed correctness check
    failed = [item for item in processed_data if not item["correct"]]
    if failed:
        print(f"\nWARNING: {len(failed)} benchmark(s) failed correctness check:")
        for item in failed:
            print(f"  - {item['benchmark']}")

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
