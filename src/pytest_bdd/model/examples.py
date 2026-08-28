from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_bdd.model.table import TableRow
    from pytest_bdd.model.tag import Tag


@frozen
class Example:
    values: tuple[str, ...] = ()
    row: TableRow | None = None
    line: int = 0
    id: str | None = None
    tags: tuple[Tag, ...] = ()
    name: str = ""


@frozen
class Examples:
    header: TableRow | None = None
    rows: tuple[TableRow, ...] = ()
    tags: tuple[Tag, ...] = ()
    name: str = ""
    keyword: str = "Examples"
    description: str = ""
    line: int = 0
    id: str | None = None

    @property
    def column_names(self) -> tuple[str, ...]:
        return self.header.values if self.header else ()

    def as_dicts(self) -> list[dict[str, str]]:
        if not self.header or not self.rows:
            return []
        return [dict(zip(self.header.values, r.values, strict=False)) for r in self.rows]


__all__ = ["Example", "Examples"]
