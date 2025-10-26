#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import seaborn as sns
import seaborn.objects as so

TYPE_ALIASES = {
    "sub": "Subprocess",
    "spec": "Speculation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot benchmark runtimes")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("plots/runtime_plot.png"),
        help="Output plot path",
    )
    parser.add_argument(
        "processed_json",
        type=Path,
        help="Processed benchmark JSON file (results/processed.json)",
    )
    return parser.parse_args()


def parse_results_to_df(processed_json: Path) -> pd.DataFrame:
    """Parse processed benchmark JSON into a DataFrame ready for plotting.

    Expects a JSON file with structure:
    [
      {
        "benchmark": "name",
        "sub_mean": float,
        "spec_mean": float,
        "correct": bool
      },
      ...
    ]

    Args:
        processed_json: Path to processed JSON file

    Returns:
        DataFrame with columns: method, runtime, benchmark, correct
    """
    with open(processed_json) as f:
        results: list[dict[str, Any]] = json.load(f)

    data: list[dict[str, str | float | bool]] = []

    for result in results:
        benchmark = result["benchmark"]
        correct = result["correct"]

        # Add row for subprocess
        data.append({
            "method": TYPE_ALIASES["sub"],
            "runtime": result["sub_mean"],
            "benchmark": benchmark,
            "correct": correct,
        })

        # Add row for speculation
        data.append({
            "method": TYPE_ALIASES["spec"],
            "runtime": result["spec_mean"],
            "benchmark": benchmark,
            "correct": correct,
        })

    return pd.DataFrame(data)


def create_plot(data: pd.DataFrame, output: Path) -> None:
    """Create and save runtime comparison plot with correctness indicators.

    Args:
        data: DataFrame with method, runtime, benchmark, correct columns
        output: Output file path
    """
    title = "Benchmark Runtime Comparison\n(shorter is better)"
    dpi = 300
    output.parent.mkdir(parents=True, exist_ok=True)

    # Add correctness symbol column
    data = data.copy()
    data["symbol"] = data["correct"].map({True: "✓", False: "✗"})
    data["symbol_color"] = data["correct"].map({True: "green", False: "red"})

    max_runtime = data["runtime"].max()

    plot = (
        so.Plot(data, x="method", y="runtime")
        .add(so.Bar(), color="method")
        # Add runtime value labels
        .add(
            so.Text(color="black", fontsize=12, valign="bottom", format="{:.1f}s"),
            y=data["runtime"] + max_runtime * 0.02,
            text="runtime",
        )
        # Add correctness symbols
        .add(
            so.Text(fontsize=16, valign="bottom"),
            y=data["runtime"] + max_runtime * 0.08,
            text="symbol",
            color="symbol_color",
        )
        .scale(color=so.Nominal(["#440154", "#31688e", "green", "red"]))
        .label(
            title=title,
            x="Execution Method",
            y="Runtime (seconds)",
        )
        .theme({**sns.axes_style("whitegrid")})
        .limit(y=(0, max_runtime * 1.2))
    )

    plot.save(output, dpi=dpi, bbox_inches="tight")
    print(f"Runtime plot saved to {output}")


def main() -> None:
    args = parse_args()

    # Parse benchmark results
    df = parse_results_to_df(args.processed_json)

    num_benchmarks = len(df) // 2  # Each benchmark has 2 rows (sub and spec)
    print(f"Loaded {num_benchmarks} benchmark(s) with {len(df)} data points")

    create_plot(df, args.output)


if __name__ == "__main__":
    main()
