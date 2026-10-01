from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, TypeAlias

from attrs import frozen

if TYPE_CHECKING:
    from pytest_cuke.model.doc_string import DocString
    from pytest_cuke.model.table import DataTable


class StepType(str, Enum):
    unknown = "Unknown"
    context = "Context"
    action = "Action"
    outcome = "Outcome"


TextSpan: TypeAlias = tuple[int, int]


@frozen
class Step:
    name: str
    keyword: str
    line: int = 0
    doc_string: DocString | None = None
    data_table: DataTable | None = None
    type: str | StepType | None = None
    id: str | None = None
    substituted_spans: tuple[TextSpan, ...] = ()

    @property
    def prefix(self) -> str:
        return self.keyword.strip().lower()

    @property
    def text(self) -> str:
        return self.name


__all__ = ["Step", "StepType"]
