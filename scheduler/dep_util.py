"""Helpers for processing streamed file dependencies from fstrace."""

import os

FILTER_PREFIXES = (
    '/tmp/pash_spec',   # hs internal temp files
    os.environ.get('HS_SANDBOX_BASE', '/hs-sandbox'),
                        # sandbox upperdirs/workdirs; try's own setup touches
                        # them on every execution — infrastructure, not a
                        # workload dependency
    '/dev',             # device files
    '/proc',            # proc filesystem
    '/sys',             # sys filesystem
    '/run',             # runtime state; includes /run/mount/utab, which the
                        # sandbox's own mount(8) calls read and write on every
                        # execution — never a real workload dependency
    '/etc/ld.so',       # dynamic linker cache/preload
    '/usr/lib/locale',  # locale data — read by every command, never written
    '/usr/share/locale',
)

# Kernel pseudo-paths (pipes, sockets, anon inodes) appear in both read and write
# sets but represent IPC, not file dependencies. Matching by substring because
# fstrace prefixes them with the cwd (e.g. /home/user/pipe:[12345]).
FILTER_SUBSTRINGS = ('pipe:[', 'socket:[', 'anon_inode:')

# Parent-directory entries that appear only because fstrace pre-computes closure
# over filtered paths (e.g. /tmp is the parent of /tmp/pash_spec/...).
FILTER_EXACT = frozenset(['/', '/tmp'])

def should_filter(path: str) -> bool:
    return (path in FILTER_EXACT
            or any(path.startswith(p) for p in FILTER_PREFIXES)
            or any(s in path for s in FILTER_SUBSTRINGS))

def read_missed(trace_file: str) -> int:
    """Read the missed-event count written by fstrace at process exit."""
    try:
        with open(trace_file + '.missed') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0
