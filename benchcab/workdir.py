# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions for generating the directory structure used for `benchcab`."""

from pathlib import Path
import os
import shutil

from benchcab import internal
from benchcab.fluxsite import Task


def clean_directory_tree(root_dir=internal.CWD):
    """Remove pre-existing directories in current working directory."""
    src_dir = Path(root_dir, internal.SRC_DIR)
    if src_dir.exists():
        shutil.rmtree(src_dir)

    run_dir = Path(root_dir, internal.RUN_DIR)
    if run_dir.exists():
        shutil.rmtree(run_dir)


def setup_src_dir(root_dir=internal.CWD):
    """Make `src` directory."""

    src_dir = Path(root_dir, internal.SRC_DIR)
    if not src_dir.exists():
        print(f"Creating {src_dir.relative_to(root_dir)} directory: {src_dir}")
        os.makedirs(src_dir)


def setup_fluxsite_directory_tree(
    fluxsite_tasks: list[Task], root_dir=internal.CWD, verbose=False
):
    """Generate the directory structure used of `benchcab`."""

    run_dir = Path(root_dir, internal.RUN_DIR)
    if not run_dir.exists():
        os.makedirs(run_dir)

    fluxsite_run_dir = Path(root_dir, internal.FLUXSITE_RUN_DIR)
    if not fluxsite_run_dir.exists():
        os.makedirs(fluxsite_run_dir)

    fluxsite_log_dir = Path(root_dir, internal.FLUXSITE_LOG_DIR)
    if not fluxsite_log_dir.exists():
        print(
            f"Creating {fluxsite_log_dir.relative_to(root_dir)} directory: {fluxsite_log_dir}"
        )
        os.makedirs(fluxsite_log_dir)

    fluxsite_output_dir = Path(root_dir, internal.FLUXSITE_OUTPUT_DIR)
    if not fluxsite_output_dir.exists():
        print(
            f"Creating {fluxsite_output_dir.relative_to(root_dir)} directory: {fluxsite_output_dir}"
        )
        os.makedirs(fluxsite_output_dir)

    fluxsite_tasks_dir = Path(root_dir, internal.FLUXSITE_TASKS_DIR)
    if not fluxsite_tasks_dir.exists():
        print(
            f"Creating {fluxsite_tasks_dir.relative_to(root_dir)} directory: {fluxsite_tasks_dir}"
        )
        os.makedirs(fluxsite_tasks_dir)

    fluxsite_analysis_dir = Path(root_dir, internal.FLUXSITE_ANALYSIS_DIR)
    if not fluxsite_analysis_dir.exists():
        print(
            f"Creating {fluxsite_analysis_dir.relative_to(root_dir)} directory: "
            f"{fluxsite_analysis_dir}"
        )
        os.makedirs(fluxsite_analysis_dir)

    fluxsite_bitwise_cmp_dir = Path(root_dir, internal.FLUXSITE_BITWISE_CMP_DIR)
    if not fluxsite_bitwise_cmp_dir.exists():
        print(
            f"Creating {fluxsite_bitwise_cmp_dir.relative_to(root_dir)} directory: "
            f"{fluxsite_bitwise_cmp_dir}"
        )
        os.makedirs(fluxsite_bitwise_cmp_dir)

    print("Creating task directories...")
    for task in fluxsite_tasks:
        task_dir = Path(root_dir, internal.FLUXSITE_TASKS_DIR, task.get_task_name())
        if not task_dir.exists():
            if verbose:
                print(f"Creating {task_dir.relative_to(root_dir)}: " f"{task_dir}")
            os.makedirs(task_dir)
