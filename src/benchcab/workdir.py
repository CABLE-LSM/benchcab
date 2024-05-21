# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Functions for generating the directory structure used for `benchcab`."""

import shutil
from pathlib import Path

from benchcab import internal
from benchcab.utils.fs import mkdir


def clean_realisation_files():
    """Remove files/directories related to CABLE realisation source codes."""
    if internal.SRC_DIR.exists():
        for realisation in internal.SRC_DIR.iterdir():
            if realisation.is_symlink():
                realisation.unlink()
        shutil.rmtree(internal.SRC_DIR)


def clean_submission_files():
    """Remove files/directories related to PBS jobs."""
    if internal.RUN_DIR.exists():
        shutil.rmtree(internal.RUN_DIR)

    if internal.STATE_DIR.exists():
        shutil.rmtree(internal.STATE_DIR)

    for pbs_job_file in Path.cwd().glob(f"{internal.QSUB_FNAME}*"):
        pbs_job_file.unlink()


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
