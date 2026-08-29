from __future__ import annotations

from typing import Any

from attrs import define

from pytest_bdd.model import (
    DataTable,
    DocString,
    Examples,
    Feature,
    Scenario,
    Step,
    TableCell,
    TableRow,
    Tag,
)
from pytest_bdd.struct_bdd.model import Join as StructJoin
from pytest_bdd.struct_bdd.model import StepPrototype as StructStep


def _build_table(struct_table: Any) -> DataTable | None:
    if not struct_table or not getattr(struct_table, "rowed_values", None):
        return None
    rows = []
    for row in struct_table.rowed_values:
        cells = tuple(TableCell(value=str(v)) for v in row)
        rows.append(TableRow(cells=cells))
    return DataTable(rows=tuple(rows)) if rows else None


def _build_examples(struct_table: Any) -> tuple[Examples, ...]:
    if not struct_table or not getattr(struct_table, "values", None) or not struct_table.values:
        return ()
    header = None
    if getattr(struct_table, "parameters", None):
        header = TableRow(cells=tuple(TableCell(value=str(p)) for p in struct_table.parameters))
    rows = tuple(TableRow(cells=tuple(TableCell(value=str(v)) for v in row)) for row in struct_table.rowed_values)
    ex_tags = tuple(Tag(name=t) for t in getattr(struct_table, "tags", []))
    ex_name = getattr(struct_table, "name", "") or ""
    return (Examples(header=header, rows=rows, tags=ex_tags, name=ex_name),)


@define
class StepToFeatureASTBuilder:
    model: StructStep

    def build_feature(self, uri: str = "", filename: str | None = None) -> Feature:
        scenarios = []
        for route in self.model.routes:
            scenario_name = next(filter(bool, [s.name for s in reversed(route.steps)]), "") or self.model.name or ""
            scenario_tags = tuple(Tag(name=t) for t in (route.tags or []))
            steps = []
            for s in route.steps:
                if s.action is not None:
                    kw = s.type.value if hasattr(s.type, "value") else str(s.type or "Given")
                    ds = DocString(content=s.description) if s.description else None
                    dt = None
                    if s.data:
                        dt = _build_table(StructJoin(tables=s.data))
                    steps.append(Step(name=s.action, keyword=kw, doc_string=ds, data_table=dt))
            examples = _build_examples(route.example_table)
            scenarios.append(
                Scenario(
                    name=scenario_name,
                    tags=scenario_tags,
                    steps=tuple(steps),
                    examples=examples,
                )
            )

        return Feature(
            name=self.model.name or "",
            description=self.model.description or "",
            tags=tuple(Tag(name=t) for t in (self.model.tags or [])),
            scenarios=tuple(scenarios),
            uri=uri,
            filename=filename,
        )


GherkinDocumentBuilder = StepToFeatureASTBuilder

__all__ = ["GherkinDocumentBuilder", "StepToFeatureASTBuilder"]
