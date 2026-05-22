"""Helpers for processing streamed file dependencies from trace_v3."""

import util

FILTER_PREFIXES = (
    '/tmp/pash_spec',   # hs internal temp files
    '/dev',             # device files
    '/proc',            # proc filesystem
    '/sys',             # sys filesystem
    '/etc/ld.so',       # dynamic linker cache/preload
    '/usr/lib/locale',  # locale data — read by every command, never written
    '/usr/share/locale',
)

# Kernel pseudo-paths (pipes, sockets, anon inodes) appear in both read and write
# sets but represent IPC, not file dependencies. Matching by substring because
# trace_v3 prefixes them with the cwd (e.g. /home/user/pipe:[12345]).
FILTER_SUBSTRINGS = ('pipe:[', 'socket:[', 'anon_inode:')

# Parent-directory entries that appear only because trace_v3 pre-computes closure
# over filtered paths (e.g. /tmp is the parent of /tmp/pash_spec/...).
FILTER_EXACT = frozenset(['/', '/tmp'])

def should_filter(path: str) -> bool:
    return (path in FILTER_EXACT
            or any(path.startswith(p) for p in FILTER_PREFIXES)
            or any(s in path for s in FILTER_SUBSTRINGS))

def read_missed(sandbox_dir: str, trace_file: str) -> int:
    """Read the missed-event count written by trace_v3 at process exit."""
    missed_path = util.sandboxed_path(sandbox_dir, trace_file + '.missed')
    try:
        with open(missed_path) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0
