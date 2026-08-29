from __future__ import annotations

from typing import Any

from pytest_bdd.model import (
    Background,
    DataTable,
    DocString,
    Step,
    TableCell,
    TableRow,
    Tag,
)


def _build_tags(tag_dicts: list[dict[str, Any]] | None) -> tuple[Tag, ...]:
    return tuple(
        Tag(
            name=t["name"],
            line=t.get("location", {}).get("line", 0),
            id=t.get("id"),
        )
        for t in (tag_dicts or [])
    )


def _build_table_row(row_dict: dict[str, Any]) -> TableRow:
    cells = tuple(
        TableCell(
            value=c.get("value", ""),
            line=c.get("location", {}).get("line", 0),
            id=c.get("id"),
        )
        for c in row_dict.get("cells", [])
    )
    return TableRow(
        cells=cells,
        line=row_dict.get("location", {}).get("line", 0),
        id=row_dict.get("id"),
    )


def _build_step(step_dict: dict[str, Any]) -> Step:
    doc_string = None
    ds = step_dict.get("docString")
    if ds:
        doc_string = DocString(
            content=ds.get("content", ""),
            media_type=ds.get("mediaType"),
            line=ds.get("location", {}).get("line", 0),
            id=ds.get("id"),
        )
    data_table = None
    dt = step_dict.get("dataTable")
    if dt:
        rows = tuple(_build_table_row(r) for r in dt.get("rows", []))
        data_table = DataTable(
            rows=rows,
            line=dt.get("location", {}).get("line", 0),
            id=dt.get("id"),
        )
    return Step(
        name=step_dict.get("text", ""),
        keyword=step_dict.get("keyword", ""),
        line=step_dict.get("location", {}).get("line", 0),
        id=step_dict.get("id"),
        type=step_dict.get("keywordType"),
        doc_string=doc_string,
        data_table=data_table,
    )


def _build_background(bg_dict: dict[str, Any]) -> Background:
    steps = tuple(_build_step(s) for s in bg_dict.get("steps", []))
    return Background(
        name=bg_dict.get("name", ""),
        keyword=bg_dict.get("keyword", "Background"),
        description=bg_dict.get("description", ""),
        line=bg_dict.get("location", {}).get("line", 0),
        id=bg_dict.get("id"),
        steps=steps,
    )


__all__ = ["_build_background", "_build_step", "_build_table_row", "_build_tags"]
