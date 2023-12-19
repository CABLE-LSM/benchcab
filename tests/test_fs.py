"""`pytest` tests for `utils/fs.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

from pathlib import Path

import pytest

from benchcab.utils.fs import mkdir, next_path


class TestNextPath:
    """Tests for `next_path()`."""

    @pytest.fixture()
    def pattern(self):
        """Return a file pattern for testing against."""
        return "rev_number-*.log"

    def test_next_path_in_empty_cwd(self, pattern):
        """Success case: get next path in 'empty' directory."""
        assert next_path(pattern) == Path("rev_number-1.log")

    def test_next_path_in_non_empty_cwd(self, pattern):
        """Success case: get next path in 'non-empty' directory."""
        next_path(pattern).touch()
        assert next_path(pattern) == Path("rev_number-2.log")


class TestMkdir:
    """Tests for `mkdir()`."""

    @pytest.mark.parametrize(
        ("test_path", "kwargs"),
        [
            (Path("test1"), {}),
            (Path("test1/test2"), dict(parents=True)),
            (Path("test1/test2"), dict(parents=True, exist_ok=True)),
        ],
    )
    def test_mkdir(self, test_path, kwargs):
        """Success case: create a test directory."""
        mkdir(test_path, **kwargs)
        assert test_path.exists()
        test_path.rmdir()
