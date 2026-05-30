"""Provide model builder helpers."""

from collections.abc import Iterable, Iterator, Sequence
from operator import attrgetter
from typing import Generic, TypeVar, cast

from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    Comment,
    DataTable,
    DocString,
    Examples,
    Feature,
    FeatureChild,
    GherkinDocument,
    Location,
    PickleStepType,
    Scenario,
    Step,
    StepKeywordType,
    TableCell,
    TableRow,
    Tag,
)

from .model import Join as StructJoin
from .model import StepPrototype as StructStep
from .model import Table as StructTable

ModelT = TypeVar("ModelT")


@define
class _ASTBuilder(Generic[ModelT]):
    model: ModelT

    def build(self, id_generator: object) -> object:  # pragma: no cover
        raise NotImplementedError


@define
class GherkinDocumentBuilder(_ASTBuilder[StructStep]):
    """Represent gherkin document builder state."""

    model: StructStep = field()

    def build(self, id_generator: object) -> GherkinDocument:
        """
        Build gherkin document.

        Returns:
            Gherkin document.

        """
        comments = [
            Comment(
                location=Location(column=1, line=index + 1),
                text=comment,
            )
            for index, comment in enumerate(self.model.comments or [])
        ]
        return GherkinDocument(
            comments=comments,
            uri=None,
            feature=StepToFeatureASTBuilder(self.model).build(id_generator=id_generator),
        )

    def build_feature(self, filename: str, uri: str | None, id_generator: object) -> GherkinDocument:  # noqa: ARG002
        """
        Build feature with filename and URI.

        Returns:
            Gherkin document with feature.

        """
        gherkin_document = self.build(id_generator=id_generator)
        gherkin_document.uri = uri
        return gherkin_document


@define
class StepToFeatureASTBuilder(_ASTBuilder[StructStep]):
    """
    Represent step to feature astbuilder state.

    Yields:
        Generated values.

    """

    model: StructStep = field()

    def build(self, id_generator: object) -> Feature:
        """
        Build feature AST.

        Returns:
            Feature AST.

        """
        return Feature(
            children=self._build_children(id_generator=id_generator),
            description=self.model.description or "",
            language="en",
            location=Location(column=1, line=1),
            tags=[],
            name=self.model.name or "",
            keyword="Feature",
        )

    def _build_children(self, id_generator: object) -> list[FeatureChild]:
        def _() -> Iterator[FeatureChild]:
            for route in self.model.routes:
                if route.steps:

                    def steps_gen(steps: Iterable[StructStep]) -> Iterator[Step]:
                        previous_step_keyword_type = None
                        for step in steps:
                            step_keyword_type = (
                                previous_step_keyword_type
                                if step.keyword_type is StepKeywordType.conjunction
                                else step.keyword_type
                            )
                            yield Step(
                                id=next(cast("Iterator[str]", id_generator)),
                                keyword=self._step_keyword(step),
                                location=Location(column=1, line=1),
                                text=self._step_action(step),
                                keyword_type=(
                                    step_keyword_type.value
                                    if step_keyword_type is not None
                                    else StepKeywordType.unknown.value
                                ),
                                **self._build_data_table(step, id_generator),
                                **(
                                    {
                                        "doc_string": DocString(
                                            content=step.description,
                                            delimiter="\n",
                                            location=Location(column=1, line=1),
                                        ),
                                    }
                                    if step.description
                                    else {}
                                ),
                            )
                            previous_step_keyword_type = step_keyword_type

                    steps = [*steps_gen(filter(lambda step: self._step_action(step) is not None, route.steps))]

                    yield FeatureChild(
                        scenario=Scenario(
                            description=route.steps[0].description or "",
                            examples=(
                                [ExampleASTBuilder(route.example_table).build(id_generator=id_generator)]
                                if route.example_table.values
                                else []
                            ),
                            id=next(cast("Iterator[str]", id_generator)),
                            keyword="Scenario",
                            location=Location(column=1, line=1),
                            name=next(
                                filter(bool, map(attrgetter("name"), reversed(route.steps))),
                                "",
                            ),
                            tags=[
                                *(
                                    Tag(
                                        id=next(cast("Iterator[str]", id_generator)),
                                        location=Location(column=1, line=1),
                                        name=tag_name,
                                    )
                                    for tag_name in route.tags or []
                                ),
                            ],
                            steps=steps,
                        ),
                    )

        return list(_())

    @staticmethod
    def _step_keyword(step: StructStep) -> str:
        return step.type if isinstance(step.type, str) else cast("PickleStepType", step.type).value

    @staticmethod
    def _step_action(step: StructStep) -> str | None:
        return cast("str | None", getattr(step, "action", None))

    @staticmethod
    def _build_data_table(step: StructStep, id_generator: object) -> dict[str, DataTable]:
        rows = [
            row
            for row in (
                StepToFeatureASTBuilder._build_data_table_row(row_values, id_generator)
                for row_values in StructJoin(tables=step.data).rowed_values
            )
            if row is not None
        ]
        return (
            {
                "data_table": DataTable(
                    rows=rows,
                    location=Location(column=1, line=1),  # type: ignore[call-arg]
                ),  # type: ignore[call-arg]
            }
            if rows
            else {}
        )

    @staticmethod
    def _build_data_table_row(row_values: Sequence[object], id_generator: object) -> TableRow | None:
        cells = [
            TableCell(
                location=Location(
                    column=1,
                    line=1,
                ),
                value=parameter,
            )
            for parameter in row_values
        ]
        return (
            TableRow(
                id=next(cast("Iterator[str]", id_generator)),
                location=Location(column=1, line=1),  # type: ignore[call-arg]
                cells=cells,
            )  # type: ignore[call-arg]
            if cells
            else None
        )


@define
class ExampleASTBuilder(_ASTBuilder[StructJoin | StructTable]):
    """Represent example astbuilder state."""

    model: StructJoin | StructTable = field()

    def build(self, id_generator: object) -> Examples:
        """
        Build examples AST.

        Returns:
            Examples AST.

        """
        return Examples(
            description=self.model.description,
            id=next(cast("Iterator[str]", id_generator)),
            keyword="Examples",
            location=Location(column=1, line=1),
            name=self.model.name,
            table_body=[
                *(
                    TableRow(
                        id=next(cast("Iterator[str]", id_generator)),
                        location=Location(column=1, line=1),
                        cells=[
                            *(
                                TableCell(
                                    location=Location(column=1, line=1),
                                    value=str(parameter),
                                )
                                for parameter in row_values
                            ),
                        ],
                    )
                    for row_values in self.model.rowed_values
                ),
            ],
            tags=[
                *(
                    Tag(
                        id=next(cast("Iterator[str]", id_generator)),
                        location=Location(column=1, line=1),
                        name=tag_name,
                    )
                    for tag_name in self.model.tags or []
                ),
            ],
            table_header=TableRow(
                id=next(cast("Iterator[str]", id_generator)),
                location=Location(column=1, line=1),
                cells=[
                    *(
                        TableCell(
                            location=Location(column=1, line=1),
                            value=parameter,
                        )
                        for parameter in self.model.parameters or []
                    ),
                ],
            ),
        )
