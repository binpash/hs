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


def create_sandbox():
    # Sandboxes must be on a filesystem separate from /tmp.  try(1) overlays
    # /tmp with an OverlayFS whose upperdir lives inside the sandbox; if the
    # sandbox is on the same tmpfs as /tmp the kernel rejects the mount
    # (upper inside lower), leaving /tmp empty in the chroot and silently
    # breaking every execution.  /dev/shm is a distinct tmpfs on virtually
    # all Linux systems.  We reuse the per-run basename from PASH_SPEC_TMP_PREFIX
    # so concurrent hs invocations stay isolated from each other.
    run_id = os.path.basename(PASH_SPEC_TMP_PREFIX)
    sandbox_base = os.path.join('/dev/shm/pash_spec', run_id)
    os.makedirs(f"{sandbox_base}/tmp/pash_spec/a", exist_ok=True)
    os.makedirs(f"{sandbox_base}/tmp/pash_spec/b", exist_ok=True)
    sdir = tempfile.mkdtemp(dir=f"{sandbox_base}/tmp/pash_spec/a", prefix="sandbox_")
    tdir = tempfile.mkdtemp(dir=f"{sandbox_base}/tmp/pash_spec/b", prefix="sandbox_")
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
