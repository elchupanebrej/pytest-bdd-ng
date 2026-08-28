from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_bdd.model.background import Background
    from pytest_bdd.model.rule import Rule
    from pytest_bdd.model.scenario import Scenario
    from pytest_bdd.model.tag import Tag


@frozen
class Feature:
    name: str
    line: int = 0
    tags: tuple[Tag, ...] = ()
    description: str = ""
    background: Background | None = None
    scenarios: tuple[Scenario, ...] = ()
    rules: tuple[Rule, ...] = ()
    uri: str = ""
    id: str | None = None
    keyword: str = "Feature"
    language: str = "en"
    filename: str | None = None

    @property
    def tag_names(self) -> tuple[str, ...]:
        return tuple(sorted(t.clean_name for t in self.tags))

    @property
    def all_scenarios(self) -> tuple[Scenario, ...]:
        return self.scenarios + tuple(s for r in self.rules for s in r.scenarios)


__all__ = ["Feature"]
