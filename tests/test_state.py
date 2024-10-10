import time
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from benchcab.utils.state import State, StateAttributeError


def test_state_is_set():
    """Success case: test state is set."""
    with TemporaryDirectory() as tmp_dir:
        state = State(state_dir=Path(tmp_dir))
        state.set("foo")
        assert state.is_set("foo")


def test_state_reset():
    """Success case: test state is reset."""
    with TemporaryDirectory() as tmp_dir:
        state = State(state_dir=Path(tmp_dir))
        state.set("foo")
        state.reset()
        assert not state.is_set("foo")


def test_state_get():
    """Success case: test get() returns the most recent state attribute."""
    with TemporaryDirectory() as tmp_dir:
        state = State(state_dir=Path(tmp_dir))
        state.set("foo")
        # This is done so that time stamps can be resolved between state attributes
        time.sleep(1)
        state.set("bar")
        assert state.get() == "bar"


def test_state_get_raises_exception():
    """Failure case: test get() raises an exception when no attributes are set."""
    with TemporaryDirectory() as tmp_dir:
        state = State(state_dir=Path(tmp_dir))
        with pytest.raises(StateAttributeError):
            state.get()
