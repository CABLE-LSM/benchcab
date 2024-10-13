"""`pytest` tests for `utils/fs.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import logging
import os
from pathlib import Path

import pytest

from benchcab.utils.fs import chdir, mkdir, next_path, prepend_path


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


class TestChdir:
    """Tests for `chdir()`."""

    @pytest.fixture(autouse=True)
    def original_cwd_path(self) -> Path:
        """Get current working directory before running any tests."""
        return Path.cwd()

    def test_chdir(self, caplog, original_cwd_path: Path, tmp_path: Path):
        """Success case: Change current working directory to `tmp_path` within context."""
        caplog.set_level(logging.DEBUG)
        assert original_cwd_path != tmp_path  # chdir should have different CWD
        assert Path.cwd() == original_cwd_path
        with chdir(tmp_path):
            log_msg = f"Changing current working directory from {original_cwd_path} to {tmp_path}"
            assert caplog.record_tuples == [("benchcab", logging.DEBUG, log_msg)]
            assert Path.cwd() == tmp_path

        assert Path.cwd() == original_cwd_path


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


class TestPrependPath:
    """Tests for `prepend_path()`."""

    var = "PATHS"
    new_path = "/path/to/bar"

    @pytest.mark.parametrize(
        ("env", "expected"),
        [
            ({}, new_path),
            (
                {var: "/path/to/foo"},
                f"{new_path}{os.pathsep}/path/to/foo",
            ),
        ],
    )
    def test_prepend_path(self, env, expected):
        """Success case: test prepend_path for unset and existing variables."""
        prepend_path(self.var, self.new_path, env=env)
        assert env[self.var] == expected
