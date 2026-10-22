from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from pytest_cuke.model.table import TableRow
    from pytest_cuke.model.tag import Tag


@frozen
class ExternalExampleRowSource:
    """The physical source row that supplied one expanded Examples row."""

    path: str
    marker_line: int
    section_index: int
    row_index: int
    source_line: int
    row_id: str | None = None


@frozen
class ExternalExamplesSource:
    """Read-only provenance for an Examples table loaded from a delimited file."""

    path: str
    marker_line: int
    section_index: int
    header_line: int
    row_lines: tuple[int, ...] = ()

    def row_source(self, row_index: int, row_id: str | None = None) -> ExternalExampleRowSource:
        """Return the physical provenance for a zero-based expanded row index."""
        return ExternalExampleRowSource(
            path=self.path,
            marker_line=self.marker_line,
            section_index=self.section_index,
            row_index=row_index + 1,
            source_line=self.row_lines[row_index],
            row_id=row_id,
        )


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
    external_source: ExternalExamplesSource | None = None

    @property
    def column_names(self) -> tuple[str, ...]:
        return self.header.values if self.header else ()

    def as_dicts(self) -> list[dict[str, str]]:
        if not self.header or not self.rows:
            return []
        return [dict(zip(self.header.values, r.values, strict=False)) for r in self.rows]


__all__ = ["Example", "Examples", "ExternalExampleRowSource", "ExternalExamplesSource"]
