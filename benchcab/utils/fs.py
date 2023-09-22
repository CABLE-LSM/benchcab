# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains utility functions for interacting with the file system."""

import os
import shutil
import contextlib
from pathlib import Path


@contextlib.contextmanager
def chdir(newdir: Path):
    """Context manager `cd`."""
    prevdir = Path.cwd()
    os.chdir(newdir.expanduser())
    try:
        yield
    finally:
        os.chdir(prevdir)


def rename(src: Path, dest: Path, verbose=False):
    """A wrapper around `pathlib.Path.rename` with optional loggging."""
    if verbose:
        print(f"mv {src} {dest}")
    src.rename(dest)


def copy2(src: Path, dest: Path, verbose=False):
    """A wrapper around `shutil.copy2` with optional logging."""
    if verbose:
        print(f"cp -p {src} {dest}")
    shutil.copy2(src, dest)
