# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing functions and data structures for running comparison tasks."""

import multiprocessing
import queue
from pathlib import Path
from subprocess import CalledProcessError


from benchcab import internal
from benchcab.utils.subprocess import SubprocessWrapperInterface, SubprocessWrapper


class ComparisonTask:
    """A class used to represent a single bitwise comparison task."""

    root_dir: Path = internal.CWD
    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        files: tuple[Path, Path],
        task_name: str,
    ) -> None:
        self.files = files
        self.task_name = task_name

    def run(self, verbose=False) -> None:
        """Executes `nccmp -df` on the NetCDF files pointed to by `self.files`."""

        file_a, file_b = self.files
        if verbose:
            print(f"Comparing files {file_a.name} and {file_b.name} bitwise...")

        try:
            self.subprocess_handler.run_cmd(
                f"nccmp -df {file_a} {file_b}",
                capture_output=True,
                verbose=verbose,
            )
            print(f"Success: files {file_a.name} {file_b.name} are identical")
        except CalledProcessError as exc:
            output_file = (
                self.root_dir
                / internal.FLUXSITE_BITWISE_CMP_DIR
                / f"{self.task_name}.txt"
            )
            with open(output_file, "w", encoding="utf-8") as file:
                file.write(exc.stdout)
            print(
                f"Failure: files {file_a.name} {file_b.name} differ. "
                f"Results of diff have been written to {output_file}"
            )


def run_comparisons(comparison_tasks: list[ComparisonTask], verbose=False) -> None:
    """Runs bitwise comparison tasks serially."""
    for task in comparison_tasks:
        task.run(verbose=verbose)


def run_comparisons_in_parallel(
    comparison_tasks: list[ComparisonTask],
    n_processes=internal.FLUXSITE_DEFAULT_PBS["ncpus"],
    verbose=False,
) -> None:
    """Runs bitwise comparison tasks in parallel across multiple processes."""

    task_queue: multiprocessing.Queue = multiprocessing.Queue()
    for task in comparison_tasks:
        task_queue.put(task)

    processes = []
    for _ in range(n_processes):
        proc = multiprocessing.Process(
            target=worker_comparison, args=[task_queue, verbose]
        )
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join()


def worker_comparison(task_queue: multiprocessing.Queue, verbose=False) -> None:
    """Runs bitwise comparison tasks in `task_queue` until the queue is emptied."""
    while True:
        try:
            task = task_queue.get_nowait()
        except queue.Empty:
            return
        task.run(verbose=verbose)
