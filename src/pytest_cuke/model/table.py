from __future__ import annotations

from attrs import frozen


@frozen
class TableCell:
    value: str
    line: int = 0
    id: str | None = None


@frozen
class TableRow:
    cells: tuple[TableCell, ...] = ()
    line: int = 0
    id: str | None = None

    @property
    def values(self) -> tuple[str, ...]:
        return tuple(c.value for c in self.cells)


@frozen
class DataTable:
    rows: tuple[TableRow, ...] = ()
    line: int = 0
    id: str | None = None

    @property
    def raw(self) -> list[list[str]]:
        return [list(r.values) for r in self.rows]

    @property
    def headings(self) -> tuple[str, ...]:
        return self.rows[0].values if self.rows else ()

    def as_dicts(self) -> list[dict[str, str]]:
        if len(self.rows) < 2:
            return []
        return [dict(zip(self.rows[0].values, r.values, strict=False)) for r in self.rows[1:]]


__all__ = ["DataTable", "TableCell", "TableRow"]
