#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.3.3",
#   "seaborn>=0.13.2",
# ]
# ///

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import seaborn.objects as so

TYPE_ALIASES = {
    "sub_mean": "Subprocess",
    "spec_mean": "Speculation",
}


dpi = 300

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
        nargs="?",
        default=Path("results/processed.json"),
        help="Processed benchmark JSON file (results/processed.json)",
    )
    return parser.parse_args()


def parse_results_to_df(processed_json: Path) -> pd.DataFrame:
    """Parse processed benchmark JSON into a long/tidy DataFrame."""

    df = pd.read_json(processed_json)

    long = df.melt(
        id_vars=["benchmark", "correct", "times_speedup"],
        value_vars=["spec_mean", "sub_mean"],
        var_name="method",
        value_name="runtime",
    )
    long.loc[long["method"] == "sub_mean", "times_speedup"] = 1.0

    long["method"] = long["method"].map(TYPE_ALIASES)

    return long


def create_plot(data: pd.DataFrame, output: Path) -> None:
    """Create and save runtime comparison plot with correctness indicators.

    Args:
        data: DataFrame with method, runtime, benchmark, correct columns
        output: Output file path
        show_correctness: If True, display correctness symbols above bars
    """
    title = "Benchmark Runtime Comparison\n(shorter is better)"

    max_runtime = data["runtime"].max()
    data["runtime_str"] = data["runtime"].round(2).astype(str) + "s"

    # Set positioning and limits for linear scale
    y_offset_speedup = data["runtime"] + max_runtime * 0.02
    y_limits = (0, max_runtime * 1.2)
    y_label = "Runtime (seconds)"
    y_scale = so.Continuous()

    # Build base plot with bars and runtime labels
    plot = (
        so.Plot(data, x="benchmark", y="runtime", color="method")
        .add(so.Bar(), so.Dodge())
        .add(
            so.Text(color="black", fontsize=10, valign="bottom"),
            so.Dodge(),
            y=y_offset_speedup,
            x="benchmark",
            text="runtime_str",
            color="method",
        )
    )

    # Apply scales, labels, theme, and limits
    plot = (
        plot.scale(
            color=so.Nominal(
                {
                    "Subprocess": "#440154",
                    "Speculation": "#31688e",
                }
            ),
            y=y_scale,
        )
        .label(title=title, x="Benchmark", y=y_label)
        .theme(sns.axes_style("whitegrid"))
        .limit(y=y_limits)
        .layout(size=(10, 6))
    )

    plot.save(output, dpi=dpi, bbox_inches="tight")
    print(f"Runtime plot saved to {output}")


def create_speedup_plot(data: pd.DataFrame, output: Path) -> None:
    """Create and save speedup comparison plot.

    Shows how many times faster speculation is compared to subprocess (normalized to 1.0).

    Args:
        data: DataFrame with method, runtime, benchmark, correct columns
        output: Output file path
        show_correctness: If True, display correctness symbols above bars
    """
    title = "Speculation Speedup vs Subprocess\n(higher is better)"

    max_speedup = data["times_speedup"].max()

    y_limits = (0, max_speedup * 1.2)
    y_label = "Speedup (×)"
    data["times_speedup"] = data["times_speedup"].round(2)

    # Color scale matching the runtime plot
    color_scale = so.Nominal(
        ["#440154", "#31688e"], order=["Subprocess", "Speculation"]
    )

    # Build plot with side-by-side bars
    plot = (
        so.Plot(data, x="benchmark", y="times_speedup", color="method")
        .add(so.Bar(), so.Dodge())
        .scale(color=color_scale)
    )

    # Apply labels, theme, and limits
    plot = (
        plot.label(title=title, x="Benchmark", y=y_label)
        .theme(sns.axes_style("whitegrid"))
        .limit(y=y_limits)
        .layout(size=(10, 6))
    )

    plot.save(output, dpi=dpi, bbox_inches="tight")
    print(f"Speedup plot saved to {output}")


def main() -> None:
    args = parse_args()

    # Parse benchmark results
    df = parse_results_to_df(args.processed_json)

    num_benchmarks = len(df) // 2  # Each benchmark has 2 rows (sub and spec)
    print(f"Loaded {num_benchmarks} benchmark(s) with {len(df)} data points")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Generate runtime comparison plot
    create_plot(df, args.output)

    # Generate speedup plot
    speedup_output = args.output.with_stem(f"{args.output.stem}_speedup")
    create_speedup_plot(df, speedup_output)


if __name__ == "__main__":
    main()
