"""Provide data table helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from cucumber_messages import DataTable  # type:ignore[attr-defined, import-untyped]


def data_table_to_dicts(data_table: DataTable | None) -> dict[str, list[str]]:
    """
    Convert a Gherkin data table to dictionaries.

    Args:
        data_table: Gherkin data table or None.

    Returns:
        Dictionary mapping first column to list of other values.

    """
    if data_table is None:
        return {}
    return {row.cells[0].value: [cell.value for cell in row.cells[1:]] for row in data_table.rows}
