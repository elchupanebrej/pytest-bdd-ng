from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import StepParser
from pytest_bdd.utils import StringableProtocol, stringify

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class string(StepParser):
    type = StepDefinitionPatternType.pytest_bdd_string_expression

    def __init__(self, name: StringableProtocol | str | bytes) -> None:
        self.name = stringify(name)

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        return {}

    @property
    def arguments(self) -> Collection[str]:
        return []

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        return bool(self.name == name)

    def __str__(self) -> str:
        return self.name
