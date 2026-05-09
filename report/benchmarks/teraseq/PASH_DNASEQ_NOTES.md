# dRNASeq PaSh Annotation And Timing Notes

## Goal

This setup adds an upstream PaSh timing path for the TERA-Seq `dRNASeq`
benchmark while preserving the existing `sh` and hS paths. The scope is only:

- `report/benchmarks/teraseq/inner/dRNASeq/run.sh`
- the cached `hsa.dRNASeq.HeLa.polyA.1` sample
- conservative PaSh annotations for commands used by that script

The full cached TERA-Seq references and FASTQs remain mounted from
`report/benchmarks/teraseq/.cache`; smoke runs use a separate sliced sample
cache so the full inputs are not modified.

## Annotation Model

PaSh command annotations describe a command's inputs, outputs, and whether it
has safe stream behavior. For this benchmark the annotations are intentionally
conservative:

- Streaming/pure commands with no custom parallelizer: `zcat`, `gzip`,
  `fastq-sanitize-header`, `minimap2`, `samtools view`, `samtools sort`,
  `seqkit grep`, `add-tag-max-sam`, and `sam-count-secondary`.
- Side-effectful or sequential fallback commands: `samtools index`,
  `sam_to_sqlite`, and `clipseqtools-preprocess`.

The local annotations are built inside the image at:

```bash
/srv/hs/pash-local-annotations
```

The tracked overlay is:

```bash
report/benchmarks/teraseq/inner/pash_annotations_overlay
```

The image copies the installed `pash_annotations` package into the local
directory and overlays these TERA-Seq additions. This is necessary because
PaSh's `--local-annotations-dir` expects a complete `pash_annotations` package,
not just a partial overlay.

## Annotation Process

The dRNASeq annotation work started from the live commands in
`report/benchmarks/teraseq/inner/dRNASeq/run.sh`. The useful command surface was
identified by scanning the active pipelines and ignoring commented-out QC and
nanopolish sections. The active pipeline commands are:

- FASTQ preprocessing: `zcat`, `fastq-sanitize-header`, `gzip`.
- Alignment and filtering: `minimap2`, `samtools view`, `samtools sort`,
  `grep`, `cut`, `sort`, `uniq`, `seqkit grep`.
- SAM postprocessing: `add-tag-max-sam`, `sam-count-secondary`.
- Database and annotation steps: `sam_to_sqlite`, `clipseqtools-preprocess`.

For each TERA-Seq-specific command, the overlay adds two PaSh annotation pieces:

- parser metadata under
  `pash_annotations/parser/command_flag_option_info/data`, which tells PaSh
  which tokens are flags, which options consume arguments, and which option
  arguments are files;
- an input/output generator under
  `pash_annotations/annotation_generation/annotation_generators`, which marks
  operands and implicit stdin/stdout use as stream inputs, stream outputs,
  config inputs, or side-effectful outputs.

The image installs upstream PaSh and `pash-annotations==0.2.4`, then runs the
overlay installer to copy the installed annotation package and overlay the local
TERA-Seq additions into:

```bash
/srv/hs/pash-local-annotations
```

The runner invokes PaSh with:

```bash
--local-annotations-dir /srv/hs/pash-local-annotations
```

This makes the local annotations visible without replacing the standard
annotations for common commands such as `grep`, `cut`, `sort`, and `uniq`.

## Safe Annotation Refinements

The local annotation overlay now models several dRNASeq commands more precisely
without adding unsafe custom parallelizers:

- `clipseqtools-preprocess`: `--database` is an `OTHER_OUTPUT`, while
  `--a_file` and `--gtf` are `CONFIG_INPUT` reference files. The command remains
  sequential because it mutates SQLite state.
- `samtools`: live `view`, `sort`, and `index` options are described explicitly.
  `view` is treated as stream input/output, `sort` remains conservative because
  it imposes global order, and `index` remains conservative because it writes an
  implicit `.bai` side-effect file.
- `seqkit grep`: `-f`/`--pattern-file` is a `CONFIG_INPUT`, `-o`/`--out-file`
  is a `STREAM_OUTPUT`, and FASTQ operands are `STREAM_INPUT`.
- `fastq-sanitize-header`: `--input FILE` is a `STREAM_INPUT`, while the
  existing `--input -` pipeline form continues to read stdin.
- `gzip`: stdin/stdout mode and `-c FILE` streaming mode are separated from
  mutating `gzip FILE` mode.

These refinements improve PaSh's dependency model and make annotation failures
easier to diagnose. They are not expected to produce major speedups for
`dRNASeq`, because the remaining wall time is dominated by internally threaded
bioinformatics tools and sequential SQLite/BED/GTF annotation steps.

## What Was Enforced

The full dRNASeq script is not run with global
`--assert_all_regions_parallelizable`. That is deliberate. The script contains
environment setup, `conda` activation/deactivation, symlink creation, file
removal, BAM indexing, SQLite writes, and database annotation commands. Treating
all of that as required-to-parallelize would be both noisy and misleading.

Instead, enforcement was checked on safe fragments. In particular, this
FASTQ-stream fragment was tested with local annotations and width 16:

```bash
pash --local-annotations-dir /srv/hs/pash-local-annotations \
  --assert_all_regions_parallelizable -w 16 \
  -c 'zcat /tmp/drna-tiny.fastq.gz | fastq-sanitize-header --input - --delim : --keep 0 | gzip > /tmp/drna-tiny.out.fastq.gz'
```

That assertion-style check exited successfully. The full smoke test then checks
end-to-end correctness by comparing return code, stdout, and output hashes
between `sh` and PaSh.

The distinction is important: the full script uses the annotations, but the
current validation only enforces them on selected safe pipeline fragments.
Database and filesystem mutation remain conservatively sequential.

## Scaling Input Size

Increasing `SMOKE_READS` or running the full FASTQ may make the timing more
representative because fixed PaSh startup and compilation overhead will be
amortized over more data. Larger input alone is still unlikely to produce a
large dRNASeq speedup with the current annotations.

The stages that grow most with input size are dominated by tools that already
manage their own parallelism or require global state:

- `minimap2 -t 6` is internally threaded.
- `samtools sort` imposes global ordering.
- `samtools index` writes implicit `.bai` side-effect files.
- `sam_to_sqlite` and `clipseqtools-preprocess` mutate a shared SQLite database.
- SAM/BAM postprocessing needs record/read-group semantics that generic line
  splitting cannot safely infer.

The only plausible current benefit area is the simple FASTQ stream
preprocessing pipeline:

```bash
zcat reads.1.fastq.gz | fastq-sanitize-header --input - --delim : --keep 0 | gzip
```

Even there, real data-parallel speedup would require a FASTQ-record-aware
splitter and safe gzip concatenation behavior. For larger speedups, the next
engineering step would be either custom FASTQ/SAM/BAM-aware PaSh parallelizers
or explicit workflow chunking/sample-level parallelism outside the conservative
annotation pass.

## Rebuild And Smoke Test

Rebuild the image and refresh cached setup state:

```bash
cd /mydata/hs/report/benchmarks/teraseq
./setup
```

Run the tiny dRNASeq smoke test with `sh` and upstream PaSh:

```bash
TERASEQ_BENCHMARKS=dRNASeq TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 ./run
```

Smoke mode creates:

```bash
report/benchmarks/teraseq/.cache/smoke/dRNASeq-1000/samples
report/benchmarks/teraseq/.cache/smoke/dRNASeq-1000/data/hg38/genes-polya.gtf
```

The smoke run still mounts the full cached reference directory, but overlays
`hg38/genes-polya.gtf` with this 5000-line slice. This keeps the final
`annotate_with_genic_elements` step from scanning the full human GTF during
smoke validation while avoiding a copy of the 111G data cache.

and writes results to:

```bash
report/output/teraseq/dRNASeq-smoke
```

Expected files after a successful smoke run:

- `sh_time`
- `sh_hash`
- `pash_time`
- `pash_log`
- `pash_stdout`
- `pash_hash`
- `error`

The `error` file should be empty. If it is non-empty, it includes the return
code, stdout, and hash differences between `sh` and PaSh.

Latest smoke artifact on disk, run on 2026-05-08 with `SMOKE_READS=1000` and
`PASH_WORKERS=16`:

- Command: `TERASEQ_BENCHMARKS=dRNASeq TERASEQ_TARGET=sh-pash TERASEQ_SMOKE=1 SMOKE_READS=1000 PASH_WORKERS=16 ./run`
- Output directory: `report/output/teraseq/dRNASeq-smoke`
- `sh_time`: `104.46140885353088`
- `pash_time`: `105.60316729545593`
- `error`: empty (`0` bytes)
- `sh_hash` and `pash_hash`: match

The small PaSh overhead in this smoke run is expected: these annotations are
safe dependency refinements, not FASTQ/SAM/BAM/SQLite custom parallelizers.

## Full Timing Command

The full benchmark is intentionally not run automatically because it can take
hours. Run it manually with:

```bash
cd /mydata/hs/report/benchmarks/teraseq
TERASEQ_BENCHMARKS=dRNASeq TERASEQ_TARGET=sh-pash PASH_WORKERS=6 ./run
```

Full-run output goes to:

```bash
report/output/teraseq/dRNASeq
```

## Validation Commands

Useful quick checks inside the built image:

```bash
docker run --rm hs/teraseq pash --help
docker run --rm hs/teraseq pash -c 'echo hi | cat'
docker run --rm hs/teraseq python -m py_compile /srv/hs/report/benchmarks/teraseq/dRNASeq/run
```

Check local annotation visibility:

```bash
docker run --rm hs/teraseq bash -lc '
PYTHONPATH=/srv/hs/pash-local-annotations python - <<PY
from pash_annotations.annotation_generation.AnnotationGeneration import DICT_CMD_NAME_TO_REPRESENTATION_IN_MODULE_NAMES as d
for cmd in ["fastq-sanitize-header", "minimap2", "samtools", "seqkit", "sam_to_sqlite"]:
    print(cmd, d.get(cmd))
PY
'
```

## Expected Failures And Debugging

- If `pash` is missing, rebuild with `./setup`; upstream PaSh is installed into
  `/srv/hs/python_pkgs/bin`.
- If a command is reported as missing input/output information, add or fix the
  matching generator and parser metadata under `pash_annotations_overlay`.
- If `samtools` appears with an absolute path, keep `dRNASeq/run.sh` using the
  `samtools` command name and ensure `$CONDA_PATH/bin` is in `PATH`.
- If the smoke hash comparison fails, inspect `report/output/teraseq/dRNASeq-smoke/error`
  first, then `pash_log`.

## Effort Estimate

- Safe annotation implementation: 2-4 engineering hours.
- Smoke validation, debugging, and report update: 1-2 elapsed hours.
- Full dRNASeq timing: likely 1-4 hours elapsed, depending on storage and CPU.
- True custom FASTQ/SAM/BAM parallelizers: 1-3 engineering days for a careful
  prototype, and longer for robust biological correctness validation.
