"""Contains classes for handling and abstracting different version control systems."""

from abc import ABC as AbstractBaseClass  # noqa: N811
from abc import abstractmethod
from pathlib import Path
from typing import Optional

import git

from benchcab import internal
from benchcab.utils import get_logger
from benchcab.utils.subprocess import SubprocessWrapper, SubprocessWrapperInterface


class Repo(AbstractBaseClass):
    """A general interface for working with code repositories.

    The interface has been designed so that it can be implemented with different
    version control systems like Git or SVN.
    """

    @abstractmethod
    def checkout(self):
        """Checkout the source code."""

    @abstractmethod
    def get_revision(self) -> str:
        """Return the latest revision of the source code.

        Returns
        -------
        str
            Human readable string describing the latest revision.

        """

    @abstractmethod
    def get_branch_name(self) -> str:
        """Return the branch name of the source code.

        Returns
        -------
        str
            Branch name of the source code.

        """


class GitRepo(Repo):
    """A concrete implementation of the `Repo` class using a Git backend.

    Attributes
    ----------
    subprocess_handler: SubprocessWrapper
        Object for handling subprocess calls.

    """

    subprocess_handler = SubprocessWrapper()

    def __init__(
        self, url: str, branch: str, path: Path, commit: Optional[str] = None
    ) -> None:
        """Return a `GitRepo` instance.

        Parameters
        ----------
        url: str
            URL pointing to the GitHub repository.
        branch: str
            Name of a branch on the GitHub repository.
        path: Path
            Path to a directory in which the repository is cloned into. If
            `path` points to an existing directory, the repository will be
            cloned into `path / branch`.
        commit: str, optional
            Commit hash (long). When specified the repository will reset to this
            commit when cloning.

        """
        self.url = url
        self.branch = branch
        self.path = path / branch if path.is_dir() else path
        self.commit = commit
        self.logger = get_logger()

    def checkout(self):
        """Checkout the source code."""
        # TODO(Sean) the gitpython package provides an interface for displaying
        # remote progress. See
        # https://gitpython.readthedocs.io/en/stable/reference.html#git.remote.RemoteProgress
        self.subprocess_handler.run_cmd(
            f"git clone --branch {self.branch} -- {self.url} {self.path}"
        )
        if self.commit:
            self.logger.debug(f"Reset to commit {self.commit} (hard reset)")
            repo = git.Repo(self.path)
            repo.head.reset(self.commit, working_tree=True)
        self.logger.info(
            f"Successfully checked out {self.branch} - {self.get_revision()}"
        )

    def get_revision(self) -> str:
        """Return the latest revision of the source code.

        Returns
        -------
        str
            Human readable string describing the latest revision.

        """
        repo = git.Repo(self.path)
        return f"commit {repo.head.commit.hexsha}"

    def get_branch_name(self) -> str:
        """Return the branch name of the source code.

        Returns
        -------
        str
            Branch name of the source code.

        """
        return self.branch


class SVNRepo(Repo):
    """A concrete implementation of the `Repo` class using an SVN backend.

    Attributes
    ----------
    subprocess_handler: SubprocessWrapper
        Object for handling subprocess calls.

    """

    subprocess_handler: SubprocessWrapperInterface = SubprocessWrapper()

    def __init__(
        self,
        svn_root: str,
        branch_path: str,
        path: Path,
        revision: Optional[int] = None,
    ) -> None:
        """Return an `SVNRepo` instance.

        Parameters
        ----------
        svn_root: str
            URL pointing to the root of the SVN repository.
        branch_path: str
            Path to a branch relative to `svn_root`.
        path: Path
            Path to a directory in which the branch is checked out into. If
            `path` points to an existing directory, the repository will be
            cloned into `path / <branch_name>` where `<branch_name>` is the
            basename of `branch_path`.
        revision: int, optional
            SVN revision number. When specified the branch will be set to this
            revision on checkout.

        """
        self.svn_root = svn_root
        self.branch_path = branch_path
        self.revision = revision
        self.path = path / Path(branch_path).name if path.is_dir() else path
        self.logger = get_logger()

    def checkout(self):
        """Checkout the source code."""
        cmd = "svn checkout"

        if self.revision:
            cmd += f" -r {self.revision}"

        cmd += f" {internal.CABLE_SVN_ROOT}/{self.branch_path} {self.path}"

        self.subprocess_handler.run_cmd(cmd)

        self.logger.info(
            f"Successfully checked out {self.path.name} - {self.get_revision()}"
        )

    def get_revision(self) -> str:
        """Return the latest revision of the source code.

        Returns
        -------
        str
            Human readable string describing the latest revision.

        """
        proc = self.subprocess_handler.run_cmd(
            f"svn info --show-item last-changed-revision {self.path}",
            capture_output=True,
        )
        return f"last-changed-revision {proc.stdout.strip()}"

    def get_branch_name(self) -> str:
        """Return the branch name of the source code.

        Returns
        -------
        str
            Branch name of the source code.

        """
        return Path(self.branch_path).name


class RepoSpecError(Exception):
    """A custom exception class for repository spec errors."""


def create_repo(spec: dict, path: Path) -> Repo:
    """A factory function which returns `Repo` objects.

    Parameters
    ----------
    spec: dict
        Specifies a repository object from the `repo` key in the benchcab
        configuration file.
    path: Path
        Path to a directory in which the repository is checked out to.

    Returns
    -------
    Repo
        A subclass instance of `Repo`.

    """
    if "git" in spec:
        if "url" not in spec["git"]:
            spec["git"]["url"] = internal.CABLE_GIT_URL
        return GitRepo(path=path, **spec["git"])
    if "svn" in spec:
        return SVNRepo(svn_root=internal.CABLE_SVN_ROOT, path=path, **spec["svn"])
    raise RepoSpecError
