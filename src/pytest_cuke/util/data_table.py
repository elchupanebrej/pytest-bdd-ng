from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cucumber_messages import DataTable


def data_table_to_dicts(data_table: DataTable | None) -> dict[str, list[str]]:
    if data_table is None:
        return {}
    return {row.cells[0].value: [cell.value for cell in row.cells[1:]] for row in data_table.rows}
