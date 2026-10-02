from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_cuke.model.background import Background
    from pytest_cuke.model.examples import Examples, ExternalExampleRowSource
    from pytest_cuke.model.step import Step
    from pytest_cuke.model.tag import Tag


@frozen
class Scenario:
    name: str
    line: int = 0
    tags: tuple[Tag, ...] = ()
    steps: tuple[Step, ...] = ()
    background: Background | None = None
    examples: tuple[Examples, ...] = ()
    id: str | None = None
    keyword: str = "Scenario"
    description: str = ""
    external_example_source: ExternalExampleRowSource | None = None
    source_ast_node_ids: tuple[str, ...] = ()

    @property
    def tag_names(self) -> tuple[str, ...]:
        return tuple(sorted(t.clean_name for t in self.tags))

    @property
    def all_steps(self) -> tuple[Step, ...]:
        return (self.background.steps if self.background else ()) + self.steps


Pickle = Scenario
__all__ = ["Pickle", "Scenario"]
