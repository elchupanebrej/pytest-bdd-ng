from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash


@runtime_checkable
class HasPytestStash(Protocol):
    stash: Stash


@runtime_checkable
class Identifiable(Protocol):
    id: Any


@runtime_checkable
class LinkedAST(Protocol):
    ast_node_id: str


@runtime_checkable
class MultiLinkedAST(Protocol):
    ast_node_ids: list[str]
