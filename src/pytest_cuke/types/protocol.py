from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from _pytest.stash import Stash


@runtime_checkable
class HasPytestStash(Protocol):
    stash: Stash


@runtime_checkable
class Identifiable(Protocol):
    id: object


@runtime_checkable
class LinkedAST(Protocol):
    ast_node_id: str


@runtime_checkable
class MultiLinkedAST(Protocol):
    ast_node_ids: list[str]


__all__ = ["HasPytestStash", "Identifiable", "LinkedAST", "MultiLinkedAST"]
