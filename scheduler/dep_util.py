"""Helpers for processing streamed file dependencies from trace_v3 FIFOs."""

import util

FILTER_PREFIXES = ('/tmp/pash_spec', '/dev')

def should_filter(path: str) -> bool:
    return any(path.startswith(p) for p in FILTER_PREFIXES)

def read_missed(sandbox_dir: str, trace_file: str) -> int:
    """Read the missed-event count written by trace_v3 at process exit."""
    missed_path = util.sandboxed_path(sandbox_dir, trace_file + '.missed')
    try:
        with open(missed_path) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0
