from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_bdd.model.step import Step


@frozen
class Background:
    name: str = ""
    line: int = 0
    steps: tuple[Step, ...] = ()
    keyword: str = "Background"
    description: str = ""
    id: str | None = None


__all__ = ["Background"]
