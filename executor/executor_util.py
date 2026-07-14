"""Standalone utilities for the executor component."""

import os
import shutil
import tempfile

PASH_SPEC_TMP_PREFIX = os.environ.get("PASH_SPEC_TMP_PREFIX", "/tmp/pash_spec/")
PASH_SPEC_TOP = os.environ.get("PASH_SPEC_TOP", "")


def ptempfile(prefix=''):
    fd, name = tempfile.mkstemp(dir=PASH_SPEC_TMP_PREFIX, prefix=prefix + '_')
    os.close(fd)
    return name


def ptempdir(prefix=''):
    return tempfile.mkdtemp(dir=PASH_SPEC_TMP_PREFIX, prefix=prefix + '_')


# Sandboxes must live somewhere try(1) never uses as an overlay lowerdir:
# the sandbox holds overlay upperdirs/workdirs, and the kernel rejects an
# overlay whose upper sits inside its own lower subtree.  try overlays every
# top-level directory except the ones the caller passes through with -B, so
# hs uses a dedicated top-level directory (created once at install time,
# e.g. `sudo mkdir -m 1777 /hs-sandbox`) and run_command.sh -B-binds it so
# try skips it.  Deliberately NOT /dev/shm: container runtimes mount that
# noexec and cap it at 64MB.
HS_SANDBOX_BASE = os.environ.get("HS_SANDBOX_BASE", "/hs-sandbox")

def create_sandbox():
    # Reuse the per-run basename from PASH_SPEC_TMP_PREFIX so concurrent hs
    # invocations stay isolated from each other.
    run_id = os.path.basename(PASH_SPEC_TMP_PREFIX)
    run_base = os.path.join(HS_SANDBOX_BASE, run_id)
    try:
        os.makedirs(f"{run_base}/a", exist_ok=True)
        os.makedirs(f"{run_base}/b", exist_ok=True)
    except (PermissionError, FileNotFoundError) as e:
        raise RuntimeError(
            f"cannot create sandboxes under {HS_SANDBOX_BASE!r}: {e}. "
            f"Create it once with: sudo mkdir -m 1777 {HS_SANDBOX_BASE}"
        ) from e
    sdir = tempfile.mkdtemp(dir=f"{run_base}/a", prefix="sandbox_")
    tdir = tempfile.mkdtemp(dir=f"{run_base}/b", prefix="sandbox_")
    return sdir, tdir


def sandboxed_path(sandbox_dir: str, path: str) -> str:
    """Return the host-side path to a file written by a process inside the sandbox.

    try(1) mounts an overlayfs for each root-level directory; writes to /foo/bar
    inside the sandbox land in {sandbox_dir}/upperdir/foo/bar on the host.
    """
    if sandbox_dir:
        return f"{sandbox_dir}/upperdir/{path}"
    return path


def copy(path_from, path_to):
    shutil.copy(path_from, path_to)
