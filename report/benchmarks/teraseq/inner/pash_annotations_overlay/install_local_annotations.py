#!/usr/bin/env python3
"""Build a local PaSh annotations tree with TERA-Seq additions."""

import importlib
import shutil
import sys
from pathlib import Path


COMMAND_REPRS = {
    "add-tag-max-sam": "AddTagMaxSam",
    "annotate-sqlite-with-fastq": "AnnotateSqliteWithFastq",
    "clipseqtools-preprocess": "ClipseqtoolsPreprocess",
    "cutadapt": "Cutadapt",
    "fastq-sanitize-header": "FastqSanitizeHeader",
    "gunzip": "Gunzip",
    "gzip": "Gzip",
    "minimap2": "Minimap2",
    "paste": "Paste",
    "sam-count-secondary": "SamCountSecondary",
    "sam_to_sqlite": "SamToSqlite",
    "samtools": "Samtools",
    "seqkit": "Seqkit",
    "seqtk": "Seqtk",
    "zcat": "Zcat",
}


def copy_installed_annotations(dest_root: Path) -> Path:
    pkg = importlib.import_module("pash_annotations")
    source = Path(pkg.__file__).resolve().parent
    dest_pkg = dest_root / "pash_annotations"
    if dest_pkg.exists():
        shutil.rmtree(dest_pkg)
    shutil.copytree(
        source,
        dest_pkg,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return dest_pkg


def overlay_teraseq_annotations(dest_pkg: Path) -> None:
    overlay_pkg = Path(__file__).resolve().parent / "pash_annotations"
    shutil.copytree(overlay_pkg, dest_pkg, dirs_exist_ok=True)


def patch_mapping(mapping_file: Path) -> None:
    text = mapping_file.read_text()
    missing = {
        cmd: repr_name
        for cmd, repr_name in COMMAND_REPRS.items()
        if f'"{cmd}"' not in text
    }
    if not missing:
        return

    marker = "DICT_CMD_NAME_TO_REPRESENTATION_IN_MODULE_NAMES = {\n"
    insertion = "".join(
        f'    "{cmd}": "{repr_name}",\n'
        for cmd, repr_name in sorted(missing.items())
    )
    if marker not in text:
        raise RuntimeError(f"Cannot find command mapping in {mapping_file}")
    mapping_file.write_text(text.replace(marker, marker + insertion, 1))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: install_local_annotations.py DEST_DIR", file=sys.stderr)
        return 2

    dest_root = Path(sys.argv[1]).resolve()
    dest_root.mkdir(parents=True, exist_ok=True)
    dest_pkg = copy_installed_annotations(dest_root)
    overlay_teraseq_annotations(dest_pkg)

    patch_mapping(dest_pkg / "annotation_generation" / "AnnotationGeneration.py")
    config_mapping = dest_pkg / "config" / "definitions.py"
    if config_mapping.exists():
        patch_mapping(config_mapping)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
