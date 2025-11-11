#!/usr/bin/env python3
"""Process benchmark results and validate output correctness."""

import filecmp
import json
import sys
from pathlib import Path
from typing import Any
import statistics


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


def get_stats(data: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "geomean_speedup": statistics.geometric_mean(v["times_speedup"] for v in data),
        "min_spec_time": min(v["spec_mean"] for v in data),
        "max_spec_time": max(v["spec_mean"] for v in data),
        "min_sub_time": min(v["sub_mean"] for v in data),
        "max_sub_time": max(v["sub_mean"] for v in data),
        "min_speedup": max(v["times_speedup"] for v in data),
        "max_speedup": max(v["times_speedup"] for v in data),
    }


def main() -> int:
    results_dir = Path("results")

    # Find all benchmark names by looking at sub-*.json files
    sub_files = list(results_dir.glob("sub-*.json"))
    processed_data = []

    for sub_file in sub_files:
        # Extract benchmark name from filename (e.g., sub-bioinfo-automine.json)
        benchmark = sub_file.stem.replace("sub-", "")
        spec_file = results_dir / f"spec-{benchmark}.json"

        if not spec_file.exists():
            print(f"Warning: Missing spec results for {benchmark}", file=sys.stderr)
            continue

        # Parse timing data
        sub_mean = parse_hyperfine_json(sub_file)
        spec_mean = parse_hyperfine_json(spec_file)
        if sub_mean is None or spec_mean is None:
            continue

        # Check output correctness
        correct = check_output_correctness(benchmark)

        processed_data.append(
            {
                "benchmark": benchmark,
                "sub_mean": sub_mean,
                "spec_mean": spec_mean,
                "correct": correct,
                "times_speedup": sub_mean / spec_mean,
            }
        )

    # get statistics
    stats = get_stats(processed_data)
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
