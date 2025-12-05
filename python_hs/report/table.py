#!/usr/bin/env python3
"""
Generate LaTeX table for Python benchmarks.

This script scans the benchmarks/ directory, uses loccount to count LOC,
calculates dataset sizes, and outputs a LaTeX table in the format of table-example.tex.
"""

import subprocess
from pathlib import Path
import json
import argparse

BENCHMARK_NAMES = {
    "biostars-multiprocessing": "BioAlign",
    "bioinfo-automine": "ProteinInt",
    "nemo-audio-processing": "AudioProc",
    "rainbowcake-python-video-processing": "VideoProc",
    "kaggle-captk-brats-preprocessing": "MRIanalysis",
}

BENCHMARK_CITATIONS = {
    "biostars-multiprocessing": "biostars-multiprocessing",
    "bioinfo-automine": "ismail2026bioinformatics",
    "nemo-audio-processing": "nemo2024",
    "rainbowcake-python-video-processing": "yu2020characterizing",
    "kaggle-captk-brats-preprocessing": "schettler2021captk",
}


def get_loc(script_path: Path) -> int:
    """Get lines of code for a script using loccount."""
    data = subprocess.run(
        ["loccount", "-j", script_path],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    for line in data.splitlines():
        lang_data = json.loads(line)
        if lang_data["language"] == "Python":
            return lang_data["sloc"]

    raise RuntimeError("Can't Parse LOC")


def get_directory_size(path) -> int:
    """Get total size of directory in bytes."""
    result = subprocess.run(
        ["du", "-sb", path], capture_output=True, text=True, check=True
    )
    # du output format: "size\tpath"
    size_bytes = int(result.stdout.split()[0])
    return size_bytes


def format_size(size_bytes):
    """Format size in bytes to human-readable format (KB, MB, GB)."""
    if size_bytes == 0:
        return "0B"

    # Define units
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)

    # Convert to appropriate unit
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Format with 1 decimal place for MB/GB, no decimals for B/KB
    if unit_index <= 1:  # B or KB
        return f"{int(size)}{units[unit_index]}"
    else:
        return f"{size:.1f}{units[unit_index]}"


def format_time(seconds: float) -> str:
    """Format time in seconds to human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m{secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h{minutes}m"


def generate_table(processed_json_path: Path | None = None) -> None:
    """Generate LaTeX table for Python benchmarks."""
    script_dir = Path(__file__).parent
    benchmarks_dir = script_dir / "benchmarks"
    data_dir = script_dir / "data"

    # Load processed.json if provided
    perf_data = {}
    if processed_json_path:
        with open(processed_json_path) as f:
            processed = json.load(f)
            for entry in processed.get("data", []):
                perf_data[entry["benchmark"]] = {
                    "baseline": entry.get("sub_mean", 0),
                    "speculative": entry.get("spec_mean", 0),
                    "speedup": entry.get("spec_speedup_compared_with_sub", 0),
                }

    # Define the order of benchmarks to match the table
    benchmark_order = [
        "biostars-multiprocessing",
        "bioinfo-automine",
        "nemo-audio-processing",
        "rainbowcake-python-video-processing",
        "kaggle-captk-brats-preprocessing",
    ]

    # Use the predefined order
    benchmark_dirs = benchmark_order

    # Collect data for each benchmark
    rows = []
    for idx, benchmark_name in enumerate(benchmark_dirs, start=1):
        # Get readable name
        readable_name = BENCHMARK_NAMES[benchmark_name]
        citation = rf"\cite{{{BENCHMARK_CITATIONS[benchmark_name]}}}"

        script_path = benchmarks_dir / benchmark_name / "subprocess_.py"
        loc = get_loc(script_path)

        # Get dataset size
        dataset_path = data_dir / benchmark_name
        size_bytes = get_directory_size(dataset_path)
        size_formatted = format_size(size_bytes)

        # Get performance data if available
        perf = perf_data.get(benchmark_name, {})
        baseline_time = perf.get("baseline", 0)
        spec_time = perf.get("speculative", 0)
        speedup = perf.get("speedup", 0)

        rows.append({
            "num": idx,
            "name": readable_name,
            "loc": loc,
            "input": size_formatted,
            "baseline_time": format_time(baseline_time) if baseline_time else "-",
            "spec_time": format_time(spec_time) if spec_time else "-",
            "speedup": f"{speedup:.2f}$\\times$" if speedup else "-",
            "cit": citation,
        })

    # Generate LaTeX table
    table_rows = "\n".join(
        rf"  {r['num']} & {r['name']}~{r['cit']:<45} & {r['loc']:<6} & {r['input']:<8} & {r['baseline_time']:<10} & {r['spec_time']:<10} & {r['speedup']} \\"
        for r in rows
    )

    table = rf"""\label{{tab:python-benchmark-summary}}
\begin{{table}}[t]
  \centering
  \caption{{Summary of all Python benchmarks used to evaluate \sys and their characteristics. Exec. Time indicates the execution time of the script with standard Python and Speedup indicates the speedup of \sys.}}
  \small
  \begin{{tabular}}{{llYYYYY}}
  \toprule
  \textbf{{~}} & \textbf{{Benchmark}} & \textbf{{LOC}} & \textbf{{Input}} & \textbf{{Baseline Time}} & \textbf{{Spec. Time}} & \textbf{{Speedup (\sys)}} \\
  \midrule
{table_rows}
  \bottomrule
  \end{{tabular}}
  \label{{tab:python_benchmark_summary}}
\end{{table}}"""

    print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate LaTeX table for Python benchmarks"
    )
    parser.add_argument(
        "--processed-json",
        type=Path,
        default=Path(__file__).parent / "results" / "processed.json",
        help="Path to processed.json file containing benchmark results (default: results/processed.json)",
    )
    args = parser.parse_args()
    generate_table(args.processed_json)
