"""`pytest` tests for `utils/fs.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

import contextlib
import io
from pathlib import Path

import pytest

from benchcab.utils.fs import mkdir, next_path

pytest.skip(allow_module_level=True)


from .common import MOCK_CWD


def test_next_path():
    """Tests for `next_path()`."""
    pattern = "rev_number-*.log"

    # Success case: get next path in 'empty' CWD
    assert len(list(MOCK_CWD.glob(pattern))) == 0
    ret = next_path(MOCK_CWD, pattern)
    assert ret == "rev_number-1.log"

    # Success case: get next path in 'non-empty' CWD
    ret_path = MOCK_CWD / ret
    ret_path.touch()
    assert len(list(MOCK_CWD.glob(pattern))) == 1
    ret = next_path(MOCK_CWD, pattern)
    assert ret == "rev_number-2.log"


@pytest.mark.parametrize(
    "test_path,kwargs",
    [
        (Path(MOCK_CWD, "test1"), {}),
        (Path(MOCK_CWD, "test1/test2"), dict(parents=True)),
        (Path(MOCK_CWD, "test1/test2"), dict(parents=True, exist_ok=True)),
    ],
)
def test_mkdir(test_path, kwargs):
    """Tests for `mkdir()`."""

    # Success case: create a test directory
    mkdir(test_path, **kwargs)
    assert test_path.exists()
    test_path.rmdir()


def test_mkdir_verbose():
    """Tests for verbose output of `mkdir()`."""

    # Success case: verbose output
    test_path = Path(MOCK_CWD, "test1")
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        mkdir(test_path, verbose=True)
    assert buf.getvalue() == (f"Creating {test_path} directory\n")
    test_path.rmdir()
