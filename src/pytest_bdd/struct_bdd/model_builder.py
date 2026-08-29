# ruff: noqa
from __future__ import annotations

from typing import Any

from attr import attrib, attrs

from messages import (  # type:ignore[attr-defined, import-untyped]
    DataTable,
    DocString,
    Examples,
    Feature,
    FeatureChild,
    GherkinDocument,
    KeywordType,
    Location,
    Scenario,
    Step,
    TableCell,
    TableRow,
    Tag,
    Type,
)
from pytest_bdd.model import (
    DataTable as L2aDataTable,
    DocString as L2aDocString,
    Examples as L2aExamples,
    Feature as L2aFeature,
    Scenario as L2aScenario,
    Step as L2aStep,
    TableCell as L2aTableCell,
    TableRow as L2aTableRow,
    Tag as L2aTag,
)
from pytest_bdd.struct_bdd.model import Join as StructJoin
from pytest_bdd.struct_bdd.model import StepPrototype as StructStep
from pytest_bdd.struct_bdd.model import Table as StructTable


def _build_table(struct_table: Any) -> L2aDataTable | None:
    if not struct_table or not getattr(struct_table, "rowed_values", None):
        return None
    rows = []
    for row in struct_table.rowed_values:
        cells = tuple(L2aTableCell(value=str(v)) for v in row)
        rows.append(L2aTableRow(cells=cells))
    return L2aDataTable(rows=tuple(rows)) if rows else None


def _build_examples(struct_table: Any) -> tuple[L2aExamples, ...]:
    if not struct_table or not getattr(struct_table, "values", None) or not struct_table.values:
        return ()
    header = None
    if getattr(struct_table, "parameters", None):
        header = L2aTableRow(cells=tuple(L2aTableCell(value=str(p)) for p in struct_table.parameters))
    rows = tuple(L2aTableRow(cells=tuple(L2aTableCell(value=str(v)) for v in row)) for row in struct_table.rowed_values)
    ex_tags = tuple(L2aTag(name=t) for t in getattr(struct_table, "tags", []))
    ex_name = getattr(struct_table, "name", "") or ""
    return (L2aExamples(header=header, rows=rows, tags=ex_tags, name=ex_name),)


@attrs
class StepToFeatureASTBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build_feature(self, uri: str = "", filename: str | None = None) -> L2aFeature:
        scenarios = []
        for route in self.model.routes:
            scenario_name = next(filter(bool, [s.name for s in reversed(route.steps)]), "") or self.model.name or ""
            scenario_tags = tuple(L2aTag(name=t) for t in (route.tags or []))
            steps = []
            for s in route.steps:
                if s.action is not None:
                    kw = s.type.value if hasattr(s.type, "value") else str(s.type or "Given")
                    ds = L2aDocString(content=s.description) if s.description else None
                    dt = None
                    if s.data:
                        dt = _build_table(StructJoin(tables=s.data))
                    steps.append(L2aStep(name=s.action, keyword=kw, doc_string=ds, data_table=dt))
            examples = _build_examples(route.example_table)
            scenarios.append(
                L2aScenario(
                    name=scenario_name,
                    tags=scenario_tags,
                    steps=tuple(steps),
                    examples=examples,
                )
            )

        return L2aFeature(
            name=self.model.name or "",
            description=self.model.description or "",
            tags=tuple(L2aTag(name=t) for t in (self.model.tags or [])),
            scenarios=tuple(scenarios),
            uri=uri,
            filename=filename,
        )


GherkinDocumentBuilder = StepToFeatureASTBuilder

__all__ = ["GherkinDocumentBuilder", "StepToFeatureASTBuilder"]
