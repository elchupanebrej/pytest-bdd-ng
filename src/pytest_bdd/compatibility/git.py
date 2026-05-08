"""Provide git helpers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from pathlib import Path


class GitCommands(Protocol):
    """Represent git commands state."""

    def config(self, *args: str) -> None:
        """Handle config."""
        ...

    def checkout(self, ref: str) -> None:
        """Handle checkout."""
        ...


class Remote(Protocol):
    """Represent remote state."""

    def fetch(self, refspec: str) -> object:
        """Fetch fetch."""
        ...


class RemoteCollection(Protocol):
    """Represent remote collection state."""

    origin: Remote


class Repo(Protocol):
    """Represent repo state."""

    git: GitCommands
    remotes: RemoteCollection

    def create_remote(self, name: str, url: str) -> Remote:
        """Create remote."""
        ...


def init_repo(path: Path) -> Repo:
    """
    Initialize a git repository at the given path.

    Args:
        path: Path to initialize the repository.

    Returns:
        Git Repo object.

    """
    git_module = import_module("git")
    repo_class = git_module.Repo
    return cast("Repo", repo_class.init(path))
