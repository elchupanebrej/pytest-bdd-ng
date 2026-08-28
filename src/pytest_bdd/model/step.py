from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_bdd.model.doc_string import DocString
    from pytest_bdd.model.table import DataTable


class StepType(str, Enum):
    unknown = "Unknown"
    context = "Context"
    action = "Action"
    outcome = "Outcome"


@frozen
class Step:
    name: str
    keyword: str
    line: int = 0
    doc_string: DocString | None = None
    data_table: DataTable | None = None
    type: str | StepType | None = None
    id: str | None = None

    @property
    def prefix(self) -> str:
        return self.keyword.strip().lower()


__all__ = ["Step", "StepType"]
