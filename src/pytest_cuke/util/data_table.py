from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence


class _Cell(Protocol):
    value: str


class _Row(Protocol):
    cells: Sequence[_Cell]


class _DataTable(Protocol):
    rows: Sequence[_Row]


def data_table_to_dicts(data_table: _DataTable | None) -> dict[str, list[str]]:
    if data_table is None:
        return {}
    return {row.cells[0].value: [cell.value for cell in row.cells[1:]] for row in data_table.rows}
