from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from attrs import frozen

from pytest_cuke.model.message_types import (
    PickleDocString,
    PickleStepArgument,
    PickleTable,
    PickleTableCell,
    PickleTableRow,
)

if TYPE_CHECKING:
    from pytest_cuke.model.doc_string import DocString
    from pytest_cuke.model.table import DataTable


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

    @property
    def text(self) -> str:
        return self.name

    @property
    def argument(self) -> PickleStepArgument | None:
        """Return the legacy Cucumber argument view without exposing mutable model state."""
        if self.doc_string is None and self.data_table is None:
            return None
        doc_index: int | None = None
        table_index: int | None = None
        if (
            self.doc_string is not None
            and self.data_table is not None
            and self.doc_string.line > 0
            and self.data_table.line > 0
            and self.doc_string.line != self.data_table.line
        ):
            doc_index = 1 if self.doc_string.line < self.data_table.line else 2
            table_index = 3 - doc_index
        return PickleStepArgument(
            doc_string=(
                PickleDocString(
                    content=self.doc_string.content, media_type=self.doc_string.media_type, argument_index=doc_index
                )
                if self.doc_string is not None
                else None
            ),
            data_table=(
                PickleTable(
                    argument_index=table_index,
                    rows=[
                        PickleTableRow(cells=[PickleTableCell(value=cell.value) for cell in row.cells])
                        for row in self.data_table.rows
                    ]
                )
                if self.data_table is not None
                else None
            ),
        )


__all__ = ["Step", "StepType"]
