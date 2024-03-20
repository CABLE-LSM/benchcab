# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for running comparison tasks."""

import multiprocessing
import operator
import sys
from pathlib import Path
from subprocess import CalledProcessError

from benchcab import internal
from benchcab.utils import get_logger
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class ComparisonTask:
    """A class used to represent a single bitwise comparison task."""

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        files: tuple[Path, Path],
        task_name: str,
    ) -> None:
        """Constructor.

        Parameters
        ----------
        files : tuple[Path, Path]
            Files.
        task_name : str
            Name of the task.

        """
        self.files = files
        self.task_name = task_name
        self.logger = get_logger()

    def run(self) -> None:
        """Executes `nccmp -df` on the NetCDF files pointed to by `self.files`."""
        file_a, file_b = self.files
        self.logger.debug(f"Comparing files {file_a.name} and {file_b.name} bitwise...")

        try:
            self.subprocess_handler.run_cmd(
                f"nccmp -df {file_a} {file_b}",
                capture_output=True,
            )
            self.logger.info(
                f"Success: files {file_a.name} {file_b.name} are identical"
            )
        except CalledProcessError as exc:
            output_file = (
                internal.FLUXSITE_DIRS["BITWISE_CMP"] / f"{self.task_name}.txt"
            )
            with output_file.open("w", encoding="utf-8") as file:
                file.write(exc.stdout)

            self.logger.error(f"Failure: files {file_a.name} {file_b.name} differ. ")
            self.logger.error(f"Results of diff have been written to {output_file}")

        sys.stdout.flush()


def run_comparisons(comparison_tasks: list[ComparisonTask]) -> None:
    """Runs bitwise comparison tasks serially."""
    for task in comparison_tasks:
        task.run()


def run_comparisons_in_parallel(
    comparison_tasks: list[ComparisonTask],
    n_processes=internal.FLUXSITE_DEFAULT_PBS["ncpus"],
) -> None:
    """Runs bitwise comparison tasks in parallel across multiple processes."""
    run_task = operator.methodcaller("run")
    with multiprocessing.Pool(n_processes) as pool:
        pool.map(run_task, comparison_tasks, chunksize=1)
