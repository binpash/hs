# 5TERA3 PaSh Annotation Notes

## Goal

This pass adds upstream PaSh coverage for the default TERA-Seq `5TERA3/run.sh` benchmark. The scope is deliberately limited to the normal three-sample run; `run_merge.sh` is left out because it adds SQLite dump/merge behavior and `samtools merge`, which need a separate conservative review.

The implementation reuses the dRNASeq PaSh setup:

- upstream PaSh is installed in the `hs/teraseq` image;
- local annotations are installed under `/srv/hs/pash-local-annotations`;
- benchmark runs call PaSh with `pash -w ${PASH_WORKERS:-6} --local-annotations-dir /srv/hs/pash-local-annotations 5TERA3/run.sh`;
- `sh-pash` runs compare return code, stdout, and output hashes.

## Annotation Process

Commands were identified by reading `report/benchmarks/teraseq/inner/5TERA3/run.sh` and comparing it with the already annotated dRNASeq command set. The shared dRNASeq annotations already cover `zcat`, `gzip`, `fastq-sanitize-header`, `minimap2`, `add-tag-max-sam`, `sam-count-secondary`, `samtools`, `seqkit grep`, `sam_to_sqlite`, and `clipseqtools-preprocess`.

The 5TERA3-specific pass adds annotations for:

- `cutadapt`: FASTQ input is `STREAM_INPUT`; `--output` and `--untrimmed-output` are `STREAM_OUTPUT`; adapter and threshold options are plain arguments; stdout is modeled because cutadapt writes its report there.
- `gunzip`: `gunzip -c FILE` is modeled as streaming input from `FILE` to stdout; mutating file mode remains conservative.
- `seqkit seq` and `seqkit subseq`: stdin or FASTQ operands are stream inputs; `-m`, `-M`, and `-r` are plain arguments; stdout is stream output unless `-o` is used.
- `seqtk subseq`: FASTQ/stdin is stream input; the read-name file is `CONFIG_INPUT`; stdout is stream output.
- `paste`: the `paste - - - -` FASTQ-record grouping idiom uses stdin and stdout, without claiming a custom parallelizer.
- `annotate-sqlite-with-fastq`: `--database` is `OTHER_OUTPUT`, `--ifile` is `STREAM_INPUT`, and DB column/table options are plain arguments.

The local annotation installer starts from the installed `pash_annotations` package, overlays the repo-tracked TERA-Seq additions, and patches PaSh's command-to-generator mapping. This keeps the image self-contained while avoiding changes to upstream PaSh.

## Conservative Commands

Several commands are intentionally modeled without aggressive parallelization by default:

- `samtools sort` imposes global order. An experimental opt-in PaSh parallelizer now exists for this command, described below, but it is not enabled unless `PASH_SAMTOOLS_SORT_PARALLEL=1` is set.
- `samtools index` writes implicit `.bai` side-effect files.
- `sam_to_sqlite`, `clipseqtools-preprocess`, and `annotate-sqlite-with-fastq` mutate SQLite databases.
- `cutadapt`, `seqkit`, `seqtk`, and FASTQ `paste` are only dependency-modeled here; no FASTQ-aware split/merge operator is added.

Because of those choices, these annotations are primarily correctness and dependency annotations. They help PaSh understand the workflow, but they do not by themselves make every stage parallel.

## Experimental `samtools sort` Aggregator

PaSh supports the common map/aggregate shape used by commands such as GNU `sort`: split input, sort chunks independently, then merge the sorted chunk outputs. For `samtools sort`, the analogous aggregator is `samtools merge`.

This pass adds an opt-in local PaSh parallelizability generator for `samtools sort`:

- enabled only with `PASH_SAMTOOLS_SORT_PARALLEL=1`;
- uses consecutive chunk splitting;
- maps each shard with `samtools sort`;
- removes mapper-local `-@`, `--threads`, and `-T` options to avoid shard oversubscription or temporary-file prefix collisions;
- aggregates coordinate-sorted shards with `samtools-sort-merge`, which runs `samtools merge --no-PG -u -@ "$SAMTOOLS_MERGE_THREADS" - ...`;
- aggregates name-sorted shards with `samtools-sort-name-merge`, which adds `samtools merge -n`;
- declines `samtools sort` invocations using `-o`, `--output`, `-O`, `--output-fmt`, `-T`, `--write-index`, or tag sort `-t`.

This is still experimental for TERA-Seq because the current pipelines often feed `samtools sort` from `samtools view -b -`, so the stream at the sort boundary is BAM. PaSh's generic splitters are not BAM-record-aware. A production-quality implementation should split SAM/BAM records with headers preserved, sort each valid shard, then merge with `samtools merge`. The opt-in exists to test PaSh's aggregator machinery and the merge strategy, not as a claim that arbitrary BAM streams are now safely parallelizable.

## Smoke Command

The smoke run slices all three 5TERA3 FASTQs on record boundaries and writes outputs under `report/output/teraseq/5TERA3-smoke`.

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=5TERA3 TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 PASH_WORKERS=16 ./run
```

Experimental `samtools sort` aggregator run:

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=5TERA3 TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 PASH_WORKERS=16 PASH_SAMTOOLS_SORT_PARALLEL=1 SAMTOOLS_MERGE_THREADS=1 ./run
```

Expected files:

- `report/output/teraseq/5TERA3-smoke/sh_time`
- `report/output/teraseq/5TERA3-smoke/pash_time`
- `report/output/teraseq/5TERA3-smoke/sh_hash`
- `report/output/teraseq/5TERA3-smoke/pash_hash`
- `report/output/teraseq/5TERA3-smoke/pash_log`
- `report/output/teraseq/5TERA3-smoke/pash_stdout`
- `report/output/teraseq/5TERA3-smoke/error`

`error` should be empty when return codes, stdout, and hashes match.

## Full Command

Do not run this automatically during annotation validation; it is the full input timing command.

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=5TERA3 TERASEQ_TARGET=sh-pash PASH_WORKERS=16 ./run
```

## Expected Performance

5TERA3 has more shell-visible FASTQ preprocessing than dRNASeq, so it is a somewhat more plausible PaSh target. The promising regions are the early streaming chains around sanitization, adapter splitting, read-name extraction, subselection, and gzip/gunzip conversion.

Major speedup is still not guaranteed. Later stages are dominated by internally threaded `minimap2`, `samtools sort/index`, and SQLite mutation. With the current safe annotations, PaSh can observe more of the workflow, but it still lacks custom FASTQ/SAM/BAM splitters and correct merge operators for biological records and sorted alignment output.

## Effort Estimate

A careful human implementation of these safe annotations is likely 3-6 engineering hours if the existing dRNASeq PaSh infrastructure is available. Smoke validation and report updates are another 1-2 elapsed hours, depending on image rebuild time and whether PaSh exposes parser edge cases. Full 5TERA3 timing is likely 2-6 elapsed hours on the current data and storage setup.

Building real performance-oriented FASTQ/SAM/BAM parallelizers would be a larger task: roughly 1-3 engineering days for a careful prototype, and longer to make the biological correctness and merge semantics robust.

## Latest Smoke Result

Recorded on May 8, 2026 after rebuilding `hs/teraseq` with the 5TERA3 annotation overlay:

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=5TERA3 TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 PASH_WORKERS=16 ./run
```

Artifacts:

- `report/output/teraseq/5TERA3-smoke/sh_time`: `324.7143819332123`
- `report/output/teraseq/5TERA3-smoke/pash_time`: `330.4193465709686`
- `report/output/teraseq/5TERA3-smoke/error`: empty
- `report/output/teraseq/5TERA3-smoke/sh_hash` and `pash_hash`: byte-identical

This smoke run validates correctness with the local annotations, but it does not show a speedup. PaSh is about 1.8% slower on this tiny slice, which is consistent with overhead plus the conservative handling of SQLite and sorted alignment stages.

Tiny fragment probes for `gunzip | seqkit | gzip`, `zcat | paste | cut | sed`, and `zcat | seqtk subseq | gzip` executed successfully through PaSh with the local annotations. Assertion-style parallelizability was not useful for these fragments because the annotations model dependencies safely but do not add FASTQ-aware parallel split/merge implementations.

## Shell Command Profile

To validate where the smoke runtime goes, the plain `sh` path was run under `strace -ff -ttt -e trace=execve` on the same `SMOKE_READS=1000` 5TERA3 sample set. The profiler records child process elapsed time from successful `execve` to process exit. These are not exclusive wall-clock stage timings, because commands inside pipelines overlap, and parent shell wrappers are excluded from the useful summary.

Artifacts:

- `report/output/teraseq/5TERA3-sh-profile/sh_wall_time`: `383.7238578796387`
- `report/output/teraseq/5TERA3-sh-profile/command_profile.tsv`
- `report/output/teraseq/5TERA3-sh-profile/category_profile.tsv`
- `report/output/teraseq/5TERA3-sh-profile/strace/`

Top command families:

| Command family | Processes | Process elapsed | % of profiled wall |
| --- | ---: | ---: | ---: |
| `clipseqtools-preprocess annotate_with_file` | 15 | 299.425s | 78.0% |
| `samtools view` | 30 | 46.194s | 12.0% |
| `samtools sort` | 18 | 43.714s | 11.4% |
| `sam-count-secondary` | 12 | 34.825s | 9.1% |
| `grep` | 19 | 32.626s | 8.5% |
| `add-tag-max-sam` | 12 | 32.263s | 8.4% |
| `minimap2 genome` | 3 | 18.597s | 4.8% |
| `clipseqtools-preprocess annotate_with_genic_elements` | 3 | 12.459s | 3.2% |

Category totals:

| Category | Process elapsed | % of profiled wall |
| --- | ---: | ---: |
| SQLite/database annotation | 327.913s | 85.5% |
| Alignment/BAM/SAM | 194.880s | 50.8% |
| Small Unix utilities | 38.859s | 10.1% |
| FASTQ preprocessing | 5.192s | 1.4% |

This supports the no-speedup hypothesis. The only currently plausible PaSh-friendly part, FASTQ preprocessing, is tiny on the smoke workload. The dominant work is SQLite/database mutation and alignment/BAM/SAM processing, much of which is either internally threaded, globally ordered, or side-effectful.

## Experimental `samtools sort` Smoke Result

Recorded on May 9, 2026 after adding the opt-in `samtools sort` mapper/aggregator:

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=5TERA3 TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 PASH_WORKERS=16 PASH_SAMTOOLS_SORT_PARALLEL=1 SAMTOOLS_MERGE_THREADS=1 ./run
```

Artifacts:

- `report/output/teraseq/5TERA3-smoke/sh_time`: `326.23230481147766`
- `report/output/teraseq/5TERA3-smoke/pash_time`: `330.6848430633545`
- `report/output/teraseq/5TERA3-smoke/error`: empty
- `report/output/teraseq/5TERA3-smoke/sh_hash` and `pash_hash`: byte-identical

The smoke rerun validates correctness but still shows no speedup. PaSh is about 1.4% slower on this tiny slice. The result is consistent with the profile above: `samtools sort` is not the dominant wall-clock bottleneck, SQLite/database mutation still dominates, and the generic PaSh splitting model is not the real SAM/BAM-aware chunking strategy needed for robust alignment parallelization.
