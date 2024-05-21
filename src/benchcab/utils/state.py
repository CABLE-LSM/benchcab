from pathlib import Path

from benchcab.internal import STATE_PREFIX


class StateAttributeError(Exception):
    """Exception class for signalling state attribute errors."""


class State:
    """Stores state which persists on the file system."""

    def __init__(self, state_dir: Path) -> None:
        """Instantiate a State object.

        Parameters
        ----------
        state_dir: Path
            Path to the directory in which state is stored. If the specified
            directory does not exist, create the directory.

        """
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def reset(self):
        """Clear all state attributes."""
        for path in self.state_dir.glob(f"{STATE_PREFIX}*"):
            path.unlink()

    def set(self, attr: str):
        """Set state attribute."""
        (self.state_dir / (STATE_PREFIX + attr)).touch()

    def is_set(self, attr: str):
        """Return True if the state attribute has been set, False otherwise."""
        return (self.state_dir / (STATE_PREFIX + attr)).exists()

    def get(self) -> str:
        """Get the state of the most recent state attribute."""
        attrs = list(self.state_dir.glob(f"{STATE_PREFIX}*"))

        def get_mtime(path: Path):
            return path.stat().st_mtime

        attrs.sort(key=get_mtime)
        try:
            return attrs.pop().name.removeprefix(STATE_PREFIX)
        except IndexError as exc:
            msg = "No attributes have been set."
            raise StateAttributeError(msg) from exc
