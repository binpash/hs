"""Which files a benchmark actually produced, and a digest over exactly those.

Comparing two runs by "every file under the output directory" is wrong in both
directions. It picks up harness artifacts and scratch files that were never the
benchmark's result, and it misses results the script wrote somewhere else. It
also calls two runs different when a format embeds a timestamp -- a gzip member
records the mtime of the data it compressed, so byte-identical input yields
byte-different output on every run.

So each test may ship an `outputs` manifest naming the files that matter:

    # Lines are glob patterns. '**' recurses. Blank lines and '#' are ignored.
    *.out
    results/**/*.txt

    # A pattern may name how to read a file before hashing it, when the bytes
    # on disk carry more than the payload:
    archive/*.gz => gzip

A pattern is resolved against the run's output directory unless it is absolute
after environment-variable expansion, which is how a benchmark that writes
outside its output directory (into a shared sample tree, say) names its results.

Manifest lookup, in order:
  1. <test_base>/outputs          -- this test's own
  2. <test_base>/../outputs       -- shared by every test in the suite
  3. the built-in default, '**/*' -- everything in the output directory

The default is what most benchmarks want and means they need no manifest at
all: the harness keeps its own artifacts outside the output directory, so
'**/*' is already exactly the program's files.

The digest is built per file rather than by streaming everything into one
archive: `tar | sha256sum` cannot apply a per-file normalizer, and tar records
mtimes and ownership that differ between runs anyway. Hashing each file and
then hashing that listing gives the same single-value comparison, plus a
listing that says precisely which file diverged.
"""

import bz2
import glob
import gzip
import hashlib
import lzma
import os
import re
from pathlib import Path

MANIFEST_NAME = "outputs"
DEFAULT_PATTERN = "**/*"

# Marker recorded in place of a digest for a file the manifest named but the
# run did not produce. Comparing listings then reports it as a difference
# instead of silently ignoring it.
MISSING = "MISSING" + "-" * 57

_ENV_VAR = re.compile(r"\$(\w+)|\$\{(\w+)\}")
_NORMALIZER_SEP = "=>"


# === Normalizers =============================================================
#
# A normalizer yields the bytes to hash for one file. The default reads the
# file as-is; the others exist because a container format stores metadata that
# changes between runs even when the payload does not.


def _normalize_raw(path):
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            yield chunk


def _decompressor(module):
    """Hash a compressed file by its contents, ignoring container metadata.

    gzip in particular stores the original mtime and filename in its header, so
    two runs that compress identical bytes still produce different files.
    """

    def normalize(path):
        with module.open(path, "rb") as f:
            while chunk := f.read(1 << 20):
                yield chunk

    return normalize


NORMALIZERS = {
    "raw": _normalize_raw,
    "gzip": _decompressor(gzip),
    "bzip2": _decompressor(bz2),
    "xz": _decompressor(lzma),
}

# Applied when a pattern does not name a normalizer explicitly.
NORMALIZER_BY_SUFFIX = {
    ".gz": "gzip",
    ".bz2": "bzip2",
    ".xz": "xz",
}


def normalizer_for(relpath, explicit=None):
    """Pick a normalizer: the pattern's choice, else the file's suffix, else raw."""
    if explicit:
        return explicit
    return NORMALIZER_BY_SUFFIX.get(Path(relpath).suffix, "raw")


# === Manifest ================================================================


class Manifest:
    """Glob patterns naming a benchmark's real output files."""

    def __init__(self, entries, source):
        # entries: list of (pattern, explicit normalizer or None)
        self.entries = entries
        self.source = source  # path the manifest came from, or a description

    def __repr__(self):
        return f"<Manifest {self.source} ({len(self.entries)} patterns)>"

    @classmethod
    def default(cls):
        return cls([(DEFAULT_PATTERN, None)], "built-in default")

    @classmethod
    def parse(cls, text, source):
        entries = []
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if _NORMALIZER_SEP in line:
                pattern, _, normalizer = line.partition(_NORMALIZER_SEP)
                pattern, normalizer = pattern.strip(), normalizer.strip()
                if normalizer not in NORMALIZERS:
                    raise ValueError(
                        f"{source}: unknown normalizer {normalizer!r}; "
                        f"known: {', '.join(sorted(NORMALIZERS))}"
                    )
            else:
                pattern, normalizer = line, None
            entries.append((pattern, normalizer))
        return cls(entries, source)

    @classmethod
    def load(cls, test_base):
        """Find the manifest for a test: its own, then its suite's, then the default."""
        test_base = Path(test_base)
        for candidate in (test_base / MANIFEST_NAME,
                          test_base.parent / MANIFEST_NAME):
            if candidate.is_file():
                return cls.parse(candidate.read_text(), str(candidate))
        return cls.default()

    def resolve(self, root, env=None):
        """Expand the patterns under `root` into a sorted list of (label, normalizer).

        The label is what identifies a file across runs: relative to `root` for
        the usual case, absolute for a file the benchmark writes elsewhere. Two
        runs with different roots therefore produce comparable labels.
        """
        root = Path(root).resolve()
        env = env if env is not None else os.environ
        found = {}
        for pattern, normalizer in self.entries:
            expanded = _expandvars(pattern, env)
            if os.path.isabs(expanded):
                matches = glob.glob(expanded, recursive=True)
            else:
                matches = glob.glob(str(root / expanded), recursive=True)
            for match in matches:
                path = Path(match)
                if not path.is_file():
                    continue
                label = _label_for(path, root)
                # First pattern to claim a file sets its normalizer, so a
                # specific rule can precede a broad one.
                found.setdefault(label, (path, normalizer))
        return sorted(
            (label, path, normalizer_for(label, normalizer))
            for label, (path, normalizer) in found.items()
        )


def _expandvars(text, env):
    def replace(match):
        name = match.group(1) or match.group(2)
        return env.get(name, match.group(0))

    return _ENV_VAR.sub(replace, text)


def _label_for(path, root):
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path.resolve())


# === Hashing =================================================================


def hash_file(path, normalizer="raw"):
    """sha256 of a file's payload, read through the named normalizer."""
    digest = hashlib.sha256()
    try:
        for chunk in NORMALIZERS[normalizer](path):
            digest.update(chunk)
    except FileNotFoundError:
        return MISSING
    return digest.hexdigest()


def hash_outputs(root, manifest, env=None):
    """Digest every file the manifest names under `root`.

    Returns a list of '<sha256> <normalizer> <label>' lines, sorted by label,
    which is both the comparison key and a readable per-file report.
    """
    lines = []
    for label, path, normalizer in manifest.resolve(root, env):
        lines.append(f"{hash_file(path, normalizer)} {normalizer:<5} {label}")
    return lines


def overall_digest(lines):
    """One digest standing for the whole listing."""
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def parse_listing(lines):
    """Turn a hash listing back into {label: digest}."""
    out = {}
    for line in lines:
        if not line.strip():
            continue
        digest, _normalizer, label = line.split(None, 2)
        out[label] = digest
    return out


def compare(sh_lines, hs_lines, sh_name="sh", hs_name="hs"):
    """Describe how two listings differ, one message per differing file."""
    sh, hs = parse_listing(sh_lines), parse_listing(hs_lines)
    messages = []

    for label in sorted(set(sh) - set(hs)):
        messages.append(f"only {sh_name} produced it: {label}")
    for label in sorted(set(hs) - set(sh)):
        messages.append(f"only {hs_name} produced it: {label}")
    for label in sorted(set(sh) & set(hs)):
        if sh[label] == hs[label]:
            continue
        if sh[label] == MISSING or hs[label] == MISSING:
            absent = sh_name if sh[label] == MISSING else hs_name
            messages.append(f"named by the manifest but absent from {absent}: {label}")
        else:
            messages.append(
                f"contents differ: {label} "
                f"({sh_name} {sh[label][:12]}, {hs_name} {hs[label][:12]})"
            )
    return messages
