# TERA-Seq PaSh Benchmark Screen

## Summary

There is no `DNASEQ` runner in this benchmark tree; the closest existing runner is `dRNASeq`, so this screen treats `DNASEQ` as `dRNASeq`.

The main result is that `dRNASeq` and `5TERA3` are not good speedup targets for current safe PaSh annotations. Their safely annotatable FASTQ work is tiny, while SQLite mutation dominates. The most promising TERA-Seq runner for further PaSh work is `mouse_SIRV`, because its smoke profile has much less SQLite time and much more time in SAM/BAM pipelines.

That promise is conditional: `mouse_SIRV` would need SAM/BAM-aware split/merge support. Plain command metadata is enough for dependency modeling, but not enough for safe or meaningful speedup of BAM/SAM pipelines.

## Measurement Method

The measured rows below come from 1000-read smoke inputs and `sh` runs profiled with:

```bash
strace -ff -ttt -s 600 -e trace=execve,exit_group
```

The parser is `report/benchmarks/teraseq/profile_strace_execs.py`. It writes:

```text
report/output/teraseq/<benchmark>-sh-profile/command_profile.tsv
report/output/teraseq/<benchmark>-sh-profile/category_profile.tsv
```

The profiles report child-process elapsed time. Pipeline stages overlap and helper processes nest, so percentages are attribution signals rather than exclusive wall-clock stage percentages. This is why some categories can exceed 100%.

## Measured Smoke Profiles

| Benchmark | Smoke samples | Profile wall | FASTQ preprocessing | Small Unix utilities | SQLite/database | Alignment/BAM/SAM | Current safe-PaSh expectation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `dRNASeq` | 1 | 122.602s | 0.44% | 9.72% | 85.02% | 48.80% | No meaningful speedup |
| `5TERA3` | 3 | 383.724s | 1.56% | 10.13% | 82.31% | 50.77% | No meaningful speedup |
| `mouse_SIRV` | 4 | 122.201s | 2.40% | 70.03% | 17.76% | 349.83% | Best candidate, but requires SAM/BAM-aware splitters |

Top bottlenecks:

| Benchmark | Largest observed command families | Interpretation |
| --- | --- | --- |
| `dRNASeq` | `clipseqtools-preprocess annotate_with_file` 80.76%, `samtools sort` 10.92%, `samtools view` 11.24% | SQLite annotation dominates; safe FASTQ work is negligible |
| `5TERA3` | `clipseqtools-preprocess annotate_with_file` 78.02%, `samtools sort` 11.39%, `samtools view` 12.04% | More FASTQ commands than dRNASeq, but still database dominated |
| `mouse_SIRV` | `samtools view` 77.69%, `samtools sort` 73.86%, `sam-count-secondary` 64.45%, `grep` 64.11%, `add-tag-max-sam` 63.38%, `minimap2 genome/SIRV` 57.93% | Runtime is in SAM/BAM pipelines; this is where a domain-aware PaSh strategy could matter |

## Speedup Bounds

Using Amdahl's law, a region with fraction `p` sped up by factor `s` gives:

```text
speedup = 1 / ((1 - p) + p / s)
```

These are optimistic bounds. For the high-percentage `mouse_SIRV` pipeline rows, process overlap means the numbers should be read as "where to investigate", not guaranteed wall-clock speedup.

| Benchmark / region | Profile share | 16-way bound | Infinite bound | Practical meaning |
| --- | ---: | ---: | ---: | --- |
| `dRNASeq` FASTQ preprocessing only | 0.44% | 1.004x | 1.004x | Current safe annotations cannot matter |
| `dRNASeq` FASTQ + small Unix | 10.16% | 1.105x | 1.113x | Still small, and much is embedded in SAM flows |
| `dRNASeq` SQLite/database | 85.02% | 4.928x | 6.676x | Dominant but unsafe without DB partition/merge redesign |
| `5TERA3` FASTQ preprocessing only | 1.56% | 1.015x | 1.016x | Adapter work remains too small on smoke |
| `5TERA3` FASTQ + small Unix | 11.69% | 1.123x | 1.132x | Not enough to overcome PaSh overhead reliably |
| `mouse_SIRV` FASTQ preprocessing only | 2.40% | 1.023x | 1.025x | Current safe annotations still too small |
| `mouse_SIRV` FASTQ + small Unix | 72.43% | 3.116x | 3.627x | Optimistic; many utilities sit inside SAM pipelines |
| `mouse_SIRV` `samtools sort` only | 73.86% | 3.251x | 3.826x | Promising only with real SAM/BAM-aware split/merge |
| `mouse_SIRV` SQLite/database | 17.76% | 1.200x | 1.216x | Much less database-bound than dRNASeq/5TERA3 |

## Static Screen Of Other Runners

| Runner | Samples | Command mix | PaSh promise |
| --- | ---: | --- | --- |
| `dRNASeq` | 1 | Few FASTQ commands; many `clipseqtools-preprocess` calls | Already measured; poor speedup target |
| `5TERA3` | 3 | Rich REL5/REL3 FASTQ preprocessing, then minimap2/samtools/SQLite | Already measured; adapter commands are still small |
| `TERA3` | 3 | Similar REL3 preprocessing to `5TERA3`, without REL5 | Reasonable next adapter-heavy smoke test, but likely similar to `5TERA3` |
| `5TERA` | 4 | REL5 preprocessing plus the same minimap2/samtools/SQLite tail | Less attractive than `TERA3`/`5TERA3` |
| `5TERA-short` | 2 | Similar to `5TERA` with fewer samples | Less attractive; same SQLite tail |
| `mouse_SIRV` | 4 | Repeated minimap2/samtools/SAM-filter pipelines and only one genic-elements annotation stage | Best candidate for further PaSh work |
| `RNASeq` | 1 | `cutadapt`, `STAR`, `samtools sort/index`; no SQLite | Interesting because no SQLite, but `STAR` is monolithic and internally threaded |
| `RiboSeq` | 1 | `cutadapt`, `STAR`, `bedtools`, duplicate marking, `sam_to_sqlite-short`, SQLite annotation | Potential SAM/BAM research target, but needs more annotations |
| `Akron5Seq` | 1 | Paired `cutadapt`, two `STAR` runs, Picard `SamToFastq`, `samtools`, SQLite annotation | Not a good plain-PaSh speedup target |

## Recommended Next Target

`mouse_SIRV` is the best follow-up if the goal is a TERA-Seq benchmark where annotated commands represent a larger part of runtime. The existing dRNASeq annotations already cover most of its command vocabulary: `zcat`, `fastq-sanitize-header`, `minimap2`, `samtools`, `seqkit grep`, `add-tag-max-sam`, `sam-count-secondary`, `sam_to_sqlite`, and `clipseqtools-preprocess`.

The low-effort implementation path is:

1. Add `pash-only` and `sh-pash` targets to `mouse_SIRV/run`, mirroring `dRNASeq/run`.
2. Add smoke-slice support for the four mouse samples and a sliced `mm10/genes-polya.gtf`.
3. Run `sh-pash` with existing annotations to validate correctness.
4. Expect little or no speedup until the SAM/BAM pipeline stages get domain-aware split/merge support.

The high-value research path is:

1. Make SAM/BAM-aware splitters that preserve headers and record boundaries.
2. Use `samtools sort` shard sort plus `samtools merge` aggregation.
3. Validate `add-tag-max-sam`, `sam-count-secondary`, and line filters under shard boundaries.
4. Only after that, retime `mouse_SIRV` and then `RiboSeq`.

## Human Effort Estimate

Adding `mouse_SIRV` PaSh runner/smoke support should take about 1-2 engineering hours because the command annotations already mostly exist.

Profiling and smoke validation should take 30-90 elapsed minutes, depending on image rebuilds and I/O.

A robust SAM/BAM-aware parallelization prototype is a larger effort: 1-3 engineering days for a careful prototype, longer for deterministic biological-correctness validation across the full TERA-Seq outputs.
