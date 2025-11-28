#!/usr/bin/env python3
"""
Generate LaTeX table for Python benchmarks.

This script scans the benchmarks/ directory, uses loccount to count LOC,
calculates dataset sizes, and outputs a LaTeX table in the format of table-example.tex.
"""

import subprocess
from pathlib import Path
import json

BENCHMARK_NAMES = {
    "biostars-multiprocessing": "Biostars Multiprocessing",
    "bioinfo-automine": "Bioinfo Automine",
    "nemo-audio-processing": "NeMo Audio Processing",
    "rainbowcake-python-video-processing": "Video Processing",
    "kaggle-captk-brats-preprocessing": "CaPTk BraTS Preprocessing",
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


def generate_table() -> None:
    """Generate LaTeX table for Python benchmarks."""
    script_dir = Path(__file__).parent
    benchmarks_dir = script_dir / "benchmarks"
    data_dir = script_dir / "data"

    benchmark_dirs = sorted([
        d.name
        for d in benchmarks_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ])

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

        rows.append({
            "num": idx,
            "name": readable_name,
            "loc": loc,
            "input": size_formatted,
            "cit": citation,
        })

    # Generate LaTeX table
    table_rows = "\n".join(
        rf"  {r['num']} & {r['name']:<40} & {r['loc']:<6} & {r['input']:<10} & {r['cit']} \\"
        for r in rows
    )

    table = rf"""\begin{{table*}}[ht]
  \centering
  \caption{{Summary of all Python benchmarks used to evaluate \sys and their characteristics.}}
  \small
  \begin{{tabularx}}{{\textwidth}}{{llrrl}}
  \toprule
  \textbf{{~}} & \textbf{{Benchmark Set}} & \textbf{{LOC}} & \textbf{{Input}} & \textbf{{Source}} \\
  \midrule
{table_rows}
  \bottomrule
  \end{{tabularx}}
  \label{{tab:python_benchmark_summary}}
\end{{table*}}"""

    print(table)


if __name__ == "__main__":
    generate_table()
