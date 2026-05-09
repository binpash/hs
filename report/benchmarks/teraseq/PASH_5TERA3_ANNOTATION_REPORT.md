# 5TERA3 PaSh Annotation Report

## Summary

The `5TERA3` benchmark now has local upstream-PaSh annotations for the default three-sample `5TERA3/run.sh` path. The annotations improve PaSh's dependency model and validate correctness against `sh`, but they do not produce a workflow speedup on the smoke input.

The short version is Amdahl's law: the commands that are safely PaSh-parallelizable today are a small fraction of the measured runtime, while the dominant work is SQLite/database mutation, alignment, and globally sorted BAM/SAM processing.

## Annotation Process

The command set was identified by reading `report/benchmarks/teraseq/inner/5TERA3/run.sh`, then comparing it with the already annotated `dRNASeq` command set. Existing shared annotations covered `zcat`, `gzip`, `fastq-sanitize-header`, `minimap2`, `samtools`, `seqkit grep`, `add-tag-max-sam`, `sam-count-secondary`, `sam_to_sqlite`, and `clipseqtools-preprocess`.

The 5TERA3-specific pass added local annotations for:

| Command | Annotation treatment | Parallelism status |
| --- | --- | --- |
| `cutadapt` | FASTQ input as `STREAM_INPUT`; `--output` and `--untrimmed-output` as `STREAM_OUTPUT`; adapter options as plain args | Dependency model only |
| `gunzip` | `gunzip -c FILE` as file stream input to stdout | Dependency model only |
| `seqkit seq` / `seqkit subseq` | FASTQ/stdin as stream input; length/range options as plain args; stdout/output file as stream output | Dependency model only |
| `seqtk subseq` | FASTQ/stdin as stream input; read-name file as `CONFIG_INPUT`; stdout as stream output | Dependency model only |
| `paste` | Supports the `paste - - - -` FASTQ-record grouping idiom as stdin/stdout | Dependency model only |
| `annotate-sqlite-with-fastq` | `--database` as `OTHER_OUTPUT`; `--ifile` as `STREAM_INPUT`; DB/table/column args as plain args | Sequential because it mutates SQLite |
| `samtools sort` | Experimental opt-in mapper/aggregator using `samtools merge` | Disabled unless `PASH_SAMTOOLS_SORT_PARALLEL=1` |

The image builds a local annotation tree by copying the installed `pash_annotations` package into `/srv/hs/pash-local-annotations`, overlaying the repo-tracked TERA-Seq additions, and patching PaSh's command-to-generator mapping. The benchmark runner invokes PaSh with:

```bash
pash -w "${PASH_WORKERS:-6}" --local-annotations-dir /srv/hs/pash-local-annotations 5TERA3/run.sh
```

## Experimental `samtools sort` Strategy

PaSh can model map/aggregate commands. GNU `sort` is the canonical example: sort chunks independently, then aggregate with `sort -m`. The analogous alignment strategy is:

```bash
# Per shard
samtools sort --no-PG -O BAM -o shard.N.bam shard.N.sam

# Coordinate-sort aggregate
samtools merge --no-PG -u -@ "$SAMTOOLS_MERGE_THREADS" - shard.1.bam shard.2.bam ...

# Name-sort aggregate
samtools merge --no-PG -n -u -@ "$SAMTOOLS_MERGE_THREADS" - shard.1.bam shard.2.bam ...
```

This report implements the PaSh-side aggregator wrapper and generator, but keeps it opt-in because the generic PaSh splitter is not SAM/BAM-record-aware. A robust version should split valid SAM/BAM records, preserve headers for every shard, sort each shard, then merge sorted shard BAMs.

## Validation

The latest opt-in smoke command was:

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=5TERA3 TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 PASH_WORKERS=16 PASH_SAMTOOLS_SORT_PARALLEL=1 SAMTOOLS_MERGE_THREADS=1 ./run
```

Results:

| Output | Value |
| --- | ---: |
| `sh_time` | `326.23230481147766` |
| `pash_time` | `330.6848430633545` |
| `error` | empty |
| `sh_hash` vs `pash_hash` | match |

This validates smoke correctness, but PaSh is about 1.4% slower on this input.

## Runtime Contribution

The plain `sh` smoke path was profiled with `strace -ff -ttt -e trace=execve`. The profile records child process elapsed time, not exclusive wall-clock stage time. Pipeline commands overlap, so the percentages below should be read as upper-bound signals about where time is spent.

Profile wall time under strace: `383.7238578796387` seconds.

Top command families:

| Command family | Process elapsed | Share of profiled wall | PaSh suitability |
| --- | ---: | ---: | --- |
| `clipseqtools-preprocess annotate_with_file` | 299.379s | 78.0% | SQLite mutation; not safe for normal PaSh splitting |
| `samtools view` | 46.194s | 12.0% | Stream command, but tied to BAM/SAM semantics |
| `samtools sort` | 43.714s | 11.4% | Mergeable only with SAM/BAM-aware splitting |
| `sam-count-secondary` | 34.802s | 9.1% | SAM-aware state/counting; needs careful semantics |
| `grep` | 32.626s | 8.5% | Line-oriented, but in SAM pipelines |
| `add-tag-max-sam` | 32.236s | 8.4% | SAM-aware transformation |
| FASTQ preprocessing category | 5.972s | 1.6% | Safest current PaSh target, but too small |

## Expected Speedup Bounds

Using Amdahl's law, if a region with fraction `p` of the profiled wall time is sped up by factor `s`, the total speedup is:

```text
speedup = 1 / ((1 - p) + p / s)
```

The table below uses the strace profile as an optimistic upper bound.

| Accelerated region | Profile share | 16x total speedup bound | Infinite speedup bound | Interpretation |
| --- | ---: | ---: | ---: | --- |
| FASTQ preprocessing only | 1.56% | 1.015x | 1.016x | Current safest PaSh-friendly work is too small to matter |
| Small Unix utilities + FASTQ | 11.69% | 1.123x | 1.132x | Optimistic; many commands are tiny or embedded in semantic pipelines |
| `samtools sort` only | 11.39% | 1.120x | 1.129x | Needs real SAM/BAM-aware split/merge to be safe and effective |
| SAM line filters (`grep`, `add-tag-max-sam`, `sam-count-secondary`) | 25.97% | 1.322x | 1.351x | Requires SAM-aware correctness, not plain text splitting |
| Sort + SAM line filters | 37.36% | 1.539x | 1.596x | Best plausible alignment-side target with custom splitters |
| Broad shell-visible stream candidates | 40.55% | 1.613x | 1.682x | Very optimistic; assumes domain-aware splitters and negligible overhead |
| SQLite/database annotation | 82.31% | 4.379x | 5.653x | Dominant, but not a safe PaSh target without redesigning DB partition/merge |

The current safe annotation set mostly falls in the first row. Even a perfect 16-way speedup of FASTQ preprocessing would save only about five seconds in the profiled smoke run. That is roughly the same scale as PaSh startup, compilation, eager/splitter, and wrapper overhead. The measured `pash_time` being a few seconds slower is therefore expected.

## Why No Speedup Was Observed

No speedup was observed for four reasons:

1. The dominant stage is SQLite/database mutation. `clipseqtools-preprocess` and related annotation steps write SQLite state and must remain sequential unless the database workflow is redesigned around partition/merge.
2. The safe FASTQ preprocessing commands are a tiny part of the smoke runtime. Their theoretical maximum impact is about 1.6%.
3. `samtools sort` is mergeable in principle, but the current workflow passes BAM streams at the sort boundary. Generic PaSh splitters do not understand BAM record boundaries or SAM headers.
4. Several candidate commands are already internally threaded or pipeline-bound. Speeding one process in a pipeline often does not reduce wall time if another process is the bottleneck.

## Practical Next Steps

The most promising performance work is not more plain annotations. It is domain-aware workflow restructuring:

- implement a SAM/BAM-aware splitter that preserves headers and record boundaries;
- sort shards with `samtools sort`, merge with `samtools merge`, and compare semantic BAM output;
- consider partitioning SQLite annotation by sample/table and merging database outputs;
- reintroduce safe sample-level parallelism outside PaSh, since 5TERA3 has three independent samples;
- keep using PaSh annotations for correctness/dependency tracking, but do not expect speedup until the domain split/merge pieces exist.

## Human Effort Estimate

The safe annotation/report work is roughly 4-8 engineering hours when the dRNASeq infrastructure already exists. Smoke validation and debugging is another 1-2 elapsed hours because the benchmark and image rebuilds are slow.

A careful prototype of SAM/BAM-aware `samtools sort` parallelization is more like 1-3 engineering days. A robust biological-correctness version, including deterministic hashes and edge-case handling, would likely take longer. SQLite partition/merge work is a separate design task.
