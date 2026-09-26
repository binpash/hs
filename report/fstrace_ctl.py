"""Load fstrace's eBPF programs around the targets that trace, never inside a
timed region and never while an untraced baseline runs.

Its tracepoints fire on every syscall of every process on the machine, so a
baseline (sh, strace) timed with them attached is slowed down by a tracer it
does not use, and hs timed with the install inside it pays for loading the
programs. Runners call load() before starting the clock on hs or fstrace and
unload() after stopping it, and unload() before starting the clock on anything
else. hs itself is told the programs are already loaded (PRELOADED_ENV) so it
does not reload them inside its own run.
"""

from pathlib import Path
from subprocess import run, PIPE, STDOUT

PIN_BASE = Path('/sys/fs/bpf/fstrace')
PRELOADED_ENV = {'HS_FSTRACE_PRELOADED': '1'}


def _fstrace(action: str):
    try:
        return run(['fstrace', action], stdout=PIPE, stderr=STDOUT, check=False)
    except FileNotFoundError:
        return None


def unload() -> None:
    """Detach fstrace's programs. Exits if they stay attached: whatever is
    timed next would be measured with every syscall traced."""
    _fstrace('uninstall')
    if PIN_BASE.exists():
        raise SystemExit(f"Error: fstrace's eBPF programs are still pinned at {PIN_BASE} "
                         "and could not be removed (not root?); refusing to time a run "
                         "with them attached.")


def load() -> bool:
    """Attach a fresh copy of fstrace's programs. Uninstalls first:
    `fstrace install` skips anything already pinned, so a stale pin from an
    older build would win silently and the tracer would record nothing."""
    unload()
    result = _fstrace('install')
    if result is None:
        print("Error: fstrace not found on PATH. Rebuild the Docker images to include fstrace.")
        return False
    if result.returncode != 0:
        print(f"Error: fstrace install failed:\n{result.stdout.decode(errors='replace')}")
        return False
    return True
