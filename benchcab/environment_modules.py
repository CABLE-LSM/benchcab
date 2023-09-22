# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""Contains a wrapper around the environment modules API."""

import sys
import contextlib
from abc import ABC as AbstractBaseClass, abstractmethod

sys.path.append("/opt/Modules/v4.3.0/init")
try:
    from python import module  # pylint: disable=import-error
except ImportError:
    print(
        "Environment modules error: unable to import "
        "initialization script for python."
    )
    # Note: cannot re-raise exception here as this will break pytest
    # when running pytest locally (outside of Gadi)


class EnvironmentModulesError(Exception):
    """Custom exception class for environment modules errors."""


class EnvironmentModulesInterface(AbstractBaseClass):
    """An abstract class (interface) that defines abstract methods for interacting
    with the environment modules API.

    An interface is defined so that we can easily mock the environment modules API
    in our unit tests.
    """

    @abstractmethod
    def module_is_avail(self, *args: str) -> bool:
        """Wrapper around `module is-avail modulefile...`"""

    @abstractmethod
    def module_is_loaded(self, *args: str) -> bool:
        """Wrapper around `module is-loaded modulefile...`"""

    @abstractmethod
    def module_load(self, *args: str) -> None:
        """Wrapper around `module load modulefile...`"""

    @abstractmethod
    def module_unload(self, *args: str) -> None:
        """Wrapper around `module unload modulefile...`"""

    @contextlib.contextmanager
    def load(self, modules: list[str], verbose=False):
        """Context manager for loading and unloading modules."""
        if verbose:
            print("Loading modules: " + " ".join(modules))
        self.module_load(*modules)
        try:
            yield
        finally:
            if verbose:
                print("Unloading modules: " + " ".join(modules))
            self.module_unload(*modules)


class EnvironmentModules(EnvironmentModulesInterface):
    """A concrete implementation of the `EnvironmentModulesInterface` abstract class."""

    def module_is_avail(self, *args: str) -> bool:
        return module("is-avail", *args)

    def module_is_loaded(self, *args: str) -> bool:
        return module("is-loaded", *args)

    def module_load(self, *args: str) -> None:
        if not module("load", *args):
            raise EnvironmentModulesError("Failed to load modules: " + " ".join(args))

    def module_unload(self, *args: str) -> None:
        if not module("unload", *args):
            raise EnvironmentModulesError("Failed to unload modules: " + " ".join(args))
