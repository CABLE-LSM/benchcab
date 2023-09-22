# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""A module containing utility functions that wraps around the `subprocess` module."""

from abc import ABC as AbstractBaseClass, abstractmethod
import subprocess
import contextlib
import pathlib
from typing import Any, Optional


class SubprocessWrapperInterface(AbstractBaseClass):
    """An abstract class (interface) that defines abstract methods for running
    subprocess commands.

    An interface is defined so that we can easily mock the subprocess API in our
    unit tests.
    """

    @abstractmethod
    def run_cmd(
        self,
        cmd: str,
        capture_output: bool = False,
        output_file: Optional[pathlib.Path] = None,
        verbose: bool = False,
        env: Optional[dict] = None,
    ) -> subprocess.CompletedProcess:
        """A wrapper around the `subprocess.run` function for executing system commands."""


class SubprocessWrapper(SubprocessWrapperInterface):
    """A concrete implementation of the `SubprocessWrapperInterface` abstract class."""

    def run_cmd(
        self,
        cmd: str,
        capture_output: bool = False,
        output_file: Optional[pathlib.Path] = None,
        verbose: bool = False,
        env: Optional[dict] = None,
    ) -> subprocess.CompletedProcess:
        kwargs: Any = {}
        with contextlib.ExitStack() as stack:
            if capture_output:
                kwargs["text"] = True
                kwargs["stdout"] = subprocess.PIPE
            elif output_file:
                kwargs["stdout"] = stack.enter_context(
                    output_file.open("w", encoding="utf-8")
                )
            else:
                kwargs["stdout"] = None if verbose else subprocess.DEVNULL
            kwargs["stderr"] = subprocess.STDOUT

            if env:
                kwargs["env"] = env

            if verbose:
                print(cmd)
            proc = subprocess.run(cmd, shell=True, check=True, **kwargs)

        return proc
