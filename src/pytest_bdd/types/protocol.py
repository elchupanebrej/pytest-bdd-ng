from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Identifiable(Protocol):
    id: object


@runtime_checkable
class LinkedAST(Protocol):
    ast_node_id: str


@runtime_checkable
class MultiLinkedAST(Protocol):
    ast_node_ids: list[str]
