from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_bdd.model.background import Background
    from pytest_bdd.model.scenario import Scenario
    from pytest_bdd.model.tag import Tag


@frozen
class Rule:
    name: str = ""
    line: int = 0
    tags: tuple[Tag, ...] = ()
    background: Background | None = None
    scenarios: tuple[Scenario, ...] = ()
    keyword: str = "Rule"
    description: str = ""
    id: str | None = None


__all__ = ["Rule"]
