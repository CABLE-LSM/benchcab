# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Functions for generating the directory structure used for `benchcab`."""

import shutil

from benchcab import internal
from benchcab.utils.fs import mkdir


def clean_directory_tree():
    """Remove pre-existing directories in current working directory."""
    if internal.SRC_DIR.exists():
        shutil.rmtree(internal.SRC_DIR)

    if internal.RUN_DIR.exists():
        shutil.rmtree(internal.RUN_DIR)


def setup_fluxsite_directory_tree():
    """Generate the directory structure used by `benchcab`."""
    for path in internal.FLUXSITE_DIRS.values():
        mkdir(path, parents=True, exist_ok=True)


def setup_spatial_directory_tree():
    """Generate the directory structure for running spatial tests."""
    for path in [
        internal.SPATIAL_RUN_DIR,
        internal.SPATIAL_TASKS_DIR,
        internal.PAYU_LABORATORY_DIR,
    ]:
        mkdir(path, parents=True, exist_ok=True)
