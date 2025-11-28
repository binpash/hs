#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.3.3",
#   "seaborn>=0.13.2",
#   "matplotlib>=3.8.0",
# ]
# ///

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

TYPE_ALIASES = {
    "sub_mean": "Subprocess",
    "spec_mean": "Speculation",
    "multi_mean": "Multiprocess",
}

BENCHMARK_NAMES = {
    "biostars-multiprocessing": "Biostars Multiprocessing",
    "bioinfo-automine": "Bioinfo Automine",
    "nemo-audio-processing": "NeMo Audio Processing",
    "rainbowcake-python-video-processing": "Video Processing",
    "kaggle-captk-brats-preprocessing": "CaPTk BraTS Preprocessing",
}

dpi = 300
# Roughly ACM single-column footprint in inches
ACM_COLUMN_SIZE = (3.35 * 2, 3.2 * 1.5)
COLOR_PALETTE = {
    "Subprocess": "#440154",
    "Speculation": "#31688e",
    "Multiprocess": "#35b779",
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
        nargs="?",
        default=Path("results/processed.json"),
        help="Processed benchmark JSON file (results/processed.json)",
    )
    return parser.parse_args()


def parse_results_to_df(processed_json: Path) -> pd.DataFrame:
    """Parse processed benchmark JSON into a long/tidy DataFrame."""

    with processed_json.open() as f:
        raw = json.load(f)

    df = pd.DataFrame(raw["data"])

    # Determine which value_vars exist (keep explicit ordering)
    value_vars = [
        col for col in ["sub_mean", "spec_mean", "multi_mean"] if col in df.columns
    ]
    if not value_vars:
        raise ValueError("No runtime columns found in processed results.")

    # Determine id_vars (exclude speedup columns as we'll recompute)
    id_vars = ["benchmark", "correct"]

    long = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="method",
        value_name="runtime",
    )

    # Drop rows with missing runtime (e.g., benchmarks without multiprocess.py)
    long = long.dropna(subset=["runtime"])

    # Compute speedup relative to subprocess baseline (or first available runtime)
    baseline_column = "sub_mean" if "sub_mean" in df.columns else value_vars[0]
    baselines = df.set_index("benchmark")[baseline_column]
    long["speedup"] = long.apply(
        lambda row: baselines[row["benchmark"]] / row["runtime"]
        if row["runtime"]
        else float("nan"),
        axis=1,
    )

    long["runtime_str"] = long["runtime"].map(lambda v: f"{v:.2f}s")
    long["speedup_str"] = long["speedup"].map(lambda v: f"{v:.2f}×")
    long["method"] = long["method"].map(TYPE_ALIASES)
    long["benchmark_name"] = (
        long["benchmark"].map(BENCHMARK_NAMES).fillna(long["benchmark"])
    )

    return long


def _benchmark_order(data: pd.DataFrame) -> list[str]:
    """Order benchmarks using readable names from table.py mapping."""
    present_ids = list(data["benchmark"].unique())
    ordered_names = [
        BENCHMARK_NAMES[b_id] for b_id in BENCHMARK_NAMES if b_id in present_ids
    ]
    extra_names = [
        data.loc[data["benchmark"] == b_id, "benchmark_name"].iat[0]
        for b_id in present_ids
        if data.loc[data["benchmark"] == b_id, "benchmark_name"].iat[0]
        not in ordered_names
    ]
    return ordered_names + extra_names


def get_runtime_labels(
    data: pd.DataFrame, benchmark_order: list[str], method: str
) -> list[str]:
    """Get runtime labels for a specific method in benchmark order."""
    labels = []
    for bench in benchmark_order:
        mask = (data["benchmark_name"] == bench) & (data["method"] == method)
        runtime = data.loc[mask, "runtime"]
        labels.append(f"{runtime.iloc[0]:.1f}s" if not runtime.empty else "")
    return labels


def create_speedup_plot(data: pd.DataFrame, output: Path) -> None:
    """Create and save speedup comparison plot."""
    sns.set_theme(style="whitegrid", rc={"figure.dpi": dpi})

    benchmark_order = _benchmark_order(data)
    methods = [m for m in TYPE_ALIASES.values() if m in data["method"].unique()]
    hue_order = [
        m for m in ["Subprocess", "Speculation", "Multiprocess"] if m in methods
    ]

    fig, ax = plt.subplots(figsize=ACM_COLUMN_SIZE)
    barplot = sns.barplot(
        data=data,
        x="benchmark_name",
        y="speedup",
        hue="method",
        hue_order=hue_order,
        order=benchmark_order,
        palette=COLOR_PALETTE,
        ax=ax,
        width=0.65,
    )

    ax.margins(y=0.1)

    for container, method in zip(ax.containers, hue_order):
        ax.bar_label(
            container,
            labels=get_runtime_labels(data, benchmark_order, method),
            fontsize=7,
        )

    max_speedup = data["speedup"].max()
    ax.set_ylim(0, max_speedup * 1.3)
    ax.set_ylabel("Speedup vs subprocess (×)", fontsize=9)
    ax.set_xlabel("")
    tick_positions = np.arange(len(benchmark_order))
    ax.set_xticks(tick_positions, benchmark_order, rotation=20, ha="right", fontsize=8)
    ax.set_title("Speedup comparison (higher is better)", fontsize=9, pad=8)
    ax.legend(title="Execution mode", fontsize=7, title_fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    print(f"Speedup plot saved to {output}")


def main() -> None:
    args = parse_args()

    # Parse benchmark results
    df = parse_results_to_df(args.processed_json)

    num_benchmarks = df["benchmark"].nunique()
    print(f"Loaded {num_benchmarks} benchmark(s) with {len(df)} data points")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    speedup_output = args.output.with_stem(f"{args.output.stem}_speedup")
    create_speedup_plot(df, speedup_output)


if __name__ == "__main__":
    main()
