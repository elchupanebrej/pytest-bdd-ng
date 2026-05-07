from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from pathlib import Path


class GitCommands(Protocol):
    def config(self, *args: str) -> None: ...

    def checkout(self, ref: str) -> None: ...


class Remote(Protocol):
    def fetch(self, refspec: str) -> object: ...


class RemoteCollection(Protocol):
    origin: Remote


class Repo(Protocol):
    git: GitCommands
    remotes: RemoteCollection

    def create_remote(self, name: str, url: str) -> Remote: ...


def init_repo(path: Path) -> Repo:
    git_module = import_module("git")
    repo_class = git_module.Repo
    return cast(Repo, repo_class.init(path))
