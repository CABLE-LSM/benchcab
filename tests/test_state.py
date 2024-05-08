import time
from pathlib import Path

import pytest
from benchcab.utils.state import State, StateAttributeError


@pytest.fixture()
def state():
    """Return a State object."""
    return State(state_dir=Path("my_state"))


def test_state_is_set(state):
    """Success case: test state is set."""
    state.set("foo")
    assert state.is_set("foo")


def test_state_reset(state):
    """Success case: test state is reset."""
    state.set("foo")
    state.reset()
    assert not state.is_set("foo")


def test_state_get(state):
    """Success case: test get() returns the most recent state attribute."""
    state.set("foo")
    # This is done so that time stamps can be resolved between state attributes
    time.sleep(0.01)
    state.set("bar")
    assert state.get() == "bar"


def test_state_get_raises_exception(state):
    """Failure case: test get() raises an exception when no attributes are set."""
    with pytest.raises(StateAttributeError):
        state.get()
