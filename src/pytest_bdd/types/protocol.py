"""Provide protocol helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Stash


@runtime_checkable
class HasPytestStash(Protocol):
    """Represent has pytest stash state."""

    stash: Stash


@runtime_checkable
class Identifiable(Protocol):
    """Represent identifiable state."""

    id: object


@runtime_checkable
class LinkedAST(Protocol):
    """Represent linked ast state."""

    ast_node_id: str


@runtime_checkable
class MultiLinkedAST(Protocol):
    """Represent multi linked ast state."""

    ast_node_ids: list[str]
