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
class _ASTBuilder:
    model: Any = attrib()

    def build(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


@attrs
class GherkinDocumentBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build_feature(self, filename: str | None = None, uri: str = "", id_generator: Any = None) -> L2aFeature:
        return StepToFeatureASTBuilder(self.model).build_feature(uri=uri, filename=filename)


@attrs
class StepToFeatureASTBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build(self, id_generator):
        return Feature(
            children=self._build_children(id_generator=id_generator),
            description=self.model.description or "",
            language="EN",
            location=Location(column=0, line=0),
            tags=[],
            name=self.model.name or "",
            keyword="Feature",
        )

    def _build_children(self, id_generator):
        def _():
            for route in self.model.routes:
                if route.steps:

                    def steps_gen(steps):
                        previous_step_keyword_type = None
                        for step in steps:
                            step_keyword_type = (
                                previous_step_keyword_type
                                if step.keyword_type is KeywordType.conjunction
                                else step.keyword_type
                            )
                            yield Step(
                                id=next(id_generator),
                                keyword=step.type if isinstance(step.type, str) else cast(Type, step.type).value,
                                location=Location(column=0, line=0),
                                text=step.action,
                                keyword_type=step_keyword_type.value,
                                **(
                                    (
                                        lambda rows: (
                                            dict(
                                                data_table=DataTable(
                                                    rows=rows,
                                                    location=Location(column=0, line=0),  # type: ignore[call-arg]
                                                )  # type: ignore[call-arg]
                                            )
                                            if rows
                                            else {}
                                        )
                                    )(
                                        [
                                            *filterfalse(
                                                lambda row: row is None,
                                                map(
                                                    lambda row_values: (
                                                        (
                                                            lambda cells: (
                                                                TableRow(
                                                                    id=next(id_generator),
                                                                    location=Location(column=0, line=0),  # type: ignore[call-arg]
                                                                    cells=cells,
                                                                )  # type: ignore[call-arg]
                                                                if cells
                                                                else None
                                                            )
                                                        )(
                                                            [
                                                                *map(
                                                                    lambda parameter: TableCell(
                                                                        location=Location(column=0, line=0),
                                                                        value=parameter,
                                                                    ),
                                                                    row_values,
                                                                )
                                                            ]
                                                        )
                                                    ),
                                                    StructJoin(tables=step.data).rowed_values,
                                                ),
                                            )
                                        ]
                                    )
                                ),
                                **(
                                    dict(
                                        doc_string=DocString(
                                            content=step.description,
                                            delimiter="\n",
                                            location=Location(column=0, line=0),
                                        )
                                    )
                                    if step.description
                                    else dict()
                                ),
                            )
                            previous_step_keyword_type = step_keyword_type

                    steps = [*steps_gen(filter(lambda step: step.action is not None, route.steps))]

                    yield FeatureChild(
                        scenario=Scenario(
                            description=route.steps[0].description or "",
                            examples=(
                                [ExampleASTBuilder(route.example_table).build(id_generator=id_generator)]
                                if route.example_table.values
                                else []
                            ),
                            id=next(id_generator),
                            keyword="Scenario",
                            location=Location(column=0, line=0),
                            name=next(filter(bool, map(attrgetter("name"), reversed(route.steps))), ""),
                            tags=[
                                *map(
                                    lambda tag_name: Tag(
                                        id=next(id_generator),
                                        location=Location(column=0, line=0),
                                        name=tag_name,
                                    ),
                                    route.tags,
                                )
                            ],
                            steps=steps,
                        )
                    )

        return list(_())


@attrs
class ExampleASTBuilder(_ASTBuilder):
    model: Union[StructJoin, StructTable] = attrib()

    def build(self, id_generator):
        return Examples(
            description=self.model.description,
            id=next(id_generator),
            keyword="Examples",
            location=Location(column=0, line=0),
            name=self.model.name,
            table_body=[
                *map(
                    lambda row_values: TableRow(
                        id=next(id_generator),
                        location=Location(column=0, line=0),
                        cells=[
                            *map(
                                lambda parameter: TableCell(
                                    location=Location(column=0, line=0),
                                    value=str(parameter),
                                ),
                                row_values,
                            )
                        ],
                    ),
                    self.model.rowed_values,
                )
            ],
            tags=[
                *map(
                    lambda tag_name: Tag(
                        id=next(id_generator),
                        location=Location(column=0, line=0),
                        name=tag_name,
                    ),
                    self.model.tags,
                )
            ],
            table_header=TableRow(
                id=next(id_generator),
                location=Location(column=0, line=0),
                cells=[
                    *map(
                        lambda parameter: TableCell(
                            location=Location(column=0, line=0),
                            value=parameter,
                        ),
                        self.model.parameters,
                    )
                ],
            ),
        )
