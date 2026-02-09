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
    os.makedirs(f"{PASH_SPEC_TMP_PREFIX}/tmp/pash_spec/a", exist_ok=True)
    os.makedirs(f"{PASH_SPEC_TMP_PREFIX}/tmp/pash_spec/b", exist_ok=True)
    sdir = tempfile.mkdtemp(dir=f"{PASH_SPEC_TMP_PREFIX}/tmp/pash_spec/a", prefix="sandbox_")
    tdir = tempfile.mkdtemp(dir=f"{PASH_SPEC_TMP_PREFIX}/tmp/pash_spec/b", prefix="sandbox_")
    return sdir, tdir


def copy(path_from, path_to):
    shutil.copy(path_from, path_to)
