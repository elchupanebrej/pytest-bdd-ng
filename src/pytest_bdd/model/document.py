from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_bdd.model.feature import Feature


@frozen
class GherkinDocument:
    uri: str = ""
    feature: Feature | None = None
    comments: tuple[str, ...] = ()
    id: str | None = None


__all__ = ["GherkinDocument"]
