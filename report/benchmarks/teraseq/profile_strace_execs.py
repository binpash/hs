#!/usr/bin/env python3
"""Summarize strace -ff execve/exit_group traces for TERA-Seq smoke runs."""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


TIMESTAMP_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s+(.*)$")
EXEC_RE = re.compile(r'execve\("([^"]+)", \[(.*)\],')
QUOTED_RE = re.compile(r'"((?:\\.|[^"\\])*)"')


def decode_c_string(value: str) -> str:
    return bytes(value, "utf-8").decode("unicode_escape")


def parse_argv(argv_blob: str) -> list[str]:
    return [decode_c_string(match.group(1)) for match in QUOTED_RE.finditer(argv_blob)]


def samtools_subcommand(argv: list[str]) -> str:
    for arg in argv[1:]:
        if not arg.startswith("-"):
            return arg
    return ""


def script_argv(argv: list[str], names: set[str]) -> tuple[str, list[str]] | None:
    for index, arg in enumerate(argv):
        base = os.path.basename(arg)
        if base in names:
            return base, argv[index + 1 :]
    return None


def teraseq_script_label(name: str, args: list[str]) -> str:
    if name == "clipseqtools-preprocess":
        if args:
            return f"clipseqtools-preprocess {args[0]}"
        return name
    if name == "seqkit" and args:
        return f"seqkit {args[0]}"
    if name == "seqtk" and args:
        return f"seqtk {args[0]}"
    if name == "annotate-sqlite-with-fastq.R":
        joined = " ".join(args)
        if "rel3" in joined:
            return "annotate-sqlite-with-fastq rel3"
        if "rel5" in joined:
            return "annotate-sqlite-with-fastq rel5"
        return "annotate-sqlite-with-fastq"
    return name


def command_label(path: str, argv: list[str]) -> str:
    base = os.path.basename(path)
    args = " ".join(argv[1:])

    if base in {"sh", "bash", "dash"}:
        return "shell/helper"
    if base in {"R", "Rscript"}:
        script = script_argv(argv, {"annotate-sqlite-with-fastq.R"})
        if script is not None:
            return teraseq_script_label(script[0], script[1])
        return "R/activation"
    if base == "conda":
        return "conda activation"
    if base == "perl":
        script = script_argv(
            argv,
            {
                "clipseqtools-preprocess",
                "fastq-sanitize-header",
                "sam_to_sqlite",
                "sam_to_sqlite-short",
            },
        )
        if script is not None:
            return teraseq_script_label(script[0], script[1])
        return "perl/helper"
    if base == "python" or base.startswith("python"):
        script = script_argv(argv, {"add-tag-max-sam", "sam-count-secondary"})
        if script is not None:
            return teraseq_script_label(script[0], script[1])
        return "python/helper"
    if base == "samtools":
        subcommand = samtools_subcommand(argv)
        return f"samtools {subcommand}".strip()
    if base == "minimap2":
        if "ensembl-transcripts-wRibo" in args:
            return "minimap2 ribosomal"
        if "transcripts.k12" in args:
            return "minimap2 transcripts"
        if "genome_sirv1" in args:
            return "minimap2 genome/SIRV"
        if "genome.k12" in args:
            return "minimap2 genome"
        return "minimap2"
    if base == "STAR":
        return "STAR"
    if base == "clipseqtools-preprocess":
        if len(argv) > 1:
            return f"clipseqtools-preprocess {argv[1]}"
        return base
    if base == "cutadapt":
        if "rel3" in args:
            return "cutadapt REL3"
        if "rel5" in args:
            return "cutadapt REL5"
        return "cutadapt"
    if base == "seqkit" and len(argv) > 1:
        return f"seqkit {argv[1]}"
    if base == "seqtk" and len(argv) > 1:
        return f"seqtk {argv[1]}"
    if base == "annotate-sqlite-with-fastq.R":
        return teraseq_script_label(base, argv[1:])
    if base == "java":
        if "SamToFastq" in args:
            return "Picard SamToFastq"
        return "java"
    return base


def category_for(label: str) -> str:
    base = label.split()[0]
    if label.startswith(("shell/", "conda ", "R/", "perl/", "python/")):
        return "environment/helper"
    if base in {
        "zcat",
        "gzip",
        "gunzip",
        "pigz",
        "fastq-sanitize-header",
        "cutadapt",
        "seqkit",
        "seqtk",
        "paste",
    }:
        return "FASTQ preprocessing"
    if base in {
        "minimap2",
        "STAR",
        "samtools",
        "add-tag-max-sam",
        "sam-count-secondary",
        "sam-mark-dups",
        "sam-mark-dups-add-count-tag",
        "bedtools",
        "Picard",
    }:
        return "alignment/BAM/SAM"
    if base in {
        "sam_to_sqlite",
        "sam_to_sqlite-short",
        "clipseqtools-preprocess",
        "annotate-sqlite-with-fastq",
    }:
        return "SQLite/database annotation"
    if base in {
        "cat",
        "cut",
        "grep",
        "head",
        "ln",
        "mv",
        "rm",
        "sed",
        "sort",
        "uniq",
        "wc",
    }:
        return "small Unix utilities"
    return "other"


def parse_trace(path: Path) -> tuple[float, str, list[str]] | None:
    exec_time = None
    exec_path = None
    argv: list[str] = []
    last_time = None

    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            timestamp_match = TIMESTAMP_RE.match(line)
            if not timestamp_match:
                continue
            timestamp = float(timestamp_match.group(1))
            payload = timestamp_match.group(2)
            last_time = timestamp

            exec_match = EXEC_RE.search(payload)
            if exec_match and payload.rstrip().endswith("= 0"):
                exec_time = timestamp
                exec_path = exec_match.group(1)
                argv = parse_argv(exec_match.group(2))

    if exec_time is None or exec_path is None or last_time is None:
        return None
    elapsed = max(0.0, last_time - exec_time)
    return elapsed, exec_path, argv


def read_wall_time(output_dir: Path, wall_time_arg: str | None) -> float | None:
    if wall_time_arg is not None:
        return float(wall_time_arg)
    for name in ("sh_wall_time", "sh_time"):
        path = output_dir / name
        if path.exists():
            return float(path.read_text(encoding="utf-8").strip())
    return None


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("strace_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--wall-time")
    args = parser.parse_args(argv)

    if not args.strace_dir.is_dir():
        parser.error(f"{args.strace_dir} is not a directory")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    wall_time = read_wall_time(args.output_dir, args.wall_time)
    command_counts: Counter[str] = Counter()
    command_elapsed: defaultdict[str, float] = defaultdict(float)
    category_elapsed: defaultdict[str, float] = defaultdict(float)

    for trace_path in sorted(path for path in args.strace_dir.iterdir() if path.is_file()):
        parsed = parse_trace(trace_path)
        if parsed is None:
            continue
        elapsed, exec_path, proc_argv = parsed
        label = command_label(exec_path, proc_argv)
        command_counts[label] += 1
        command_elapsed[label] += elapsed
        category_elapsed[category_for(label)] += elapsed

    if wall_time is None:
        wall_time = max(command_elapsed.values(), default=0.0)

    command_rows = []
    for label, elapsed in sorted(command_elapsed.items(), key=lambda item: item[1], reverse=True):
        command_rows.append(
            {
                "command": label,
                "processes": command_counts[label],
                "elapsed_process_seconds": f"{elapsed:.6f}",
                "percent_of_wall": f"{(elapsed / wall_time * 100) if wall_time else 0:.2f}",
            }
        )

    category_rows = []
    for label, elapsed in sorted(category_elapsed.items(), key=lambda item: item[1], reverse=True):
        category_rows.append(
            {
                "category": label,
                "elapsed_process_seconds": f"{elapsed:.6f}",
                "percent_of_wall": f"{(elapsed / wall_time * 100) if wall_time else 0:.2f}",
            }
        )

    write_tsv(
        args.output_dir / "command_profile.tsv",
        command_rows,
        ["command", "processes", "elapsed_process_seconds", "percent_of_wall"],
    )
    write_tsv(
        args.output_dir / "category_profile.tsv",
        category_rows,
        ["category", "elapsed_process_seconds", "percent_of_wall"],
    )
    (args.output_dir / "profile_wall_time").write_text(f"{wall_time}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
