"""`pytest` tests for `workdir.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

from pathlib import Path

import pytest

from benchcab.workdir import (
    clean_directory_tree,
    setup_fluxsite_directory_tree,
)


class TestSetupFluxsiteDirectoryTree:
    """Tests for `setup_fluxsite_directory_tree()`."""

    @pytest.fixture(autouse=True)
    def fluxsite_directory_list(self):
        """Return the list of work directories we want benchcab to create."""
        return [
            Path("runs", "fluxsite"),
            Path("runs", "fluxsite", "logs"),
            Path("runs", "fluxsite", "outputs"),
            Path("runs", "fluxsite", "tasks"),
            Path("runs", "fluxsite", "analysis"),
            Path("runs", "fluxsite", "analysis", "bitwise-comparisons"),
        ]

    def test_directory_structure_generated(self, fluxsite_directory_list):
        """Success case: generate the full fluxsite directory structure."""
        setup_fluxsite_directory_tree()
        for path in fluxsite_directory_list:
            assert path.exists()


class TestCleanDirectoryTree:
    """Tests for `clean_directory_tree()`."""

    @pytest.mark.parametrize("test_path", [Path("runs"), Path("src")])
    def test_clean_directory_tree(self, test_path):
        """Success case: directory tree does not exist after clean."""
        test_path.mkdir()
        clean_directory_tree()
        assert not test_path.exists()
