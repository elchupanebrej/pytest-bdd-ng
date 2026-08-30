from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

    @property
    def pickles(self) -> tuple[Scenario, ...]:
        return self.all_scenarios

    @property
    def rel_filename(self) -> str:
        from pathlib import Path

        if self.filename:
            try:
                return Path(self.filename).relative_to(Path.cwd()).as_posix()
            except ValueError:
                return Path(self.filename).as_posix()
        if self.uri.startswith("file:"):
            return self.uri[5:]
        return self.uri

    def _get_pickle_line_number(self, pickle: Scenario) -> int:
        return pickle.line

    def _get_step_line_number(self, step: Any) -> int:
        return getattr(step, "line", 0)


__all__ = ["Feature"]
