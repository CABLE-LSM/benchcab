"""`pytest` tests for `utils/fs.py`."""

import pytest

pytest.skip(allow_module_level=True)

from benchcab.utils.fs import next_path

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
