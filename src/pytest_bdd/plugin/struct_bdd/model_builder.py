import json
from itertools import filterfalse
from json import loads as json_loads
from operator import attrgetter
from typing import Any, cast

from attr import attrib, attrs
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
from gherkin.pickles.compiler import Compiler

from pytest_bdd.model.gherkin_document import Feature as GherkinDocumentFeature
from pytest_bdd.model.message_converter import message_converter

from .model import Join as StructJoin
from .model import StepPrototype as StructStep
from .model import Table as StructTable


@attrs
class _ASTBuilder:
    model: Any

    def build(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


@attrs
class GherkinDocumentBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build(self, id_generator):
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

    def build_feature(self, filename, uri, id_generator):
        gherkin_document = self.build(id_generator=id_generator)
        gherkin_document.uri = uri

        gherkin_document_serialized = json.dumps(message_converter.to_dict(gherkin_document))

        scenarios_data = Compiler().compile(json_loads(gherkin_document_serialized))
        pickles = GherkinDocumentFeature.load_pickles(scenarios_data)

        feature = GherkinDocumentFeature(  # type: ignore[call-arg]
            gherkin_document=gherkin_document,
            uri=uri,
            pickles=pickles,
            filename=filename,
        )

        feature.fill_registry()

        return feature


@attrs
class StepToFeatureASTBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build(self, id_generator):
        return Feature(
            children=self._build_children(id_generator=id_generator),
            description=self.model.description or "",
            language="en",
            location=Location(column=1, line=1),
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
                                if step.keyword_type is StepKeywordType.conjunction
                                else step.keyword_type
                            )
                            yield Step(
                                id=next(id_generator),
                                keyword=(
                                    step.type if isinstance(step.type, str) else cast(PickleStepType, step.type).value
                                ),
                                location=Location(column=1, line=1),
                                text=step.action,
                                keyword_type=step_keyword_type.value,
                                **(
                                    (
                                        lambda rows: (
                                            {
                                                "data_table": DataTable(
                                                    rows=rows,
                                                    location=Location(column=1, line=1),  # type: ignore[call-arg]
                                                ),  # type: ignore[call-arg]
                                            }
                                            if rows
                                            else {}
                                        )
                                    )(
                                        [
                                            *filterfalse(
                                                lambda row: row is None,
                                                (
                                                    (
                                                        (
                                                            lambda cells: (
                                                                TableRow(
                                                                    id=next(id_generator),
                                                                    location=Location(column=1, line=1),  # type: ignore[call-arg]
                                                                    cells=cells,
                                                                )  # type: ignore[call-arg]
                                                                if cells
                                                                else None
                                                            )
                                                        )(
                                                            [
                                                                *(
                                                                    TableCell(
                                                                        location=Location(
                                                                            column=1,
                                                                            line=1,
                                                                        ),
                                                                        value=parameter,
                                                                    )
                                                                    for parameter in row_values
                                                                ),
                                                            ],
                                                        )
                                                    )
                                                    for row_values in StructJoin(tables=step.data).rowed_values
                                                ),
                                            ),
                                        ],
                                    )
                                ),
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
                            location=Location(column=1, line=1),
                            name=next(
                                filter(bool, map(attrgetter("name"), reversed(route.steps))),
                                "",
                            ),
                            tags=[
                                *(
                                    Tag(
                                        id=next(id_generator),
                                        location=Location(column=1, line=1),
                                        name=tag_name,
                                    )
                                    for tag_name in route.tags
                                ),
                            ],
                            steps=steps,
                        ),
                    )

        return list(_())


@attrs
class ExampleASTBuilder(_ASTBuilder):
    model: StructJoin | StructTable = attrib()

    def build(self, id_generator):
        return Examples(
            description=self.model.description,
            id=next(id_generator),
            keyword="Examples",
            location=Location(column=1, line=1),
            name=self.model.name,
            table_body=[
                *(
                    TableRow(
                        id=next(id_generator),
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
                        id=next(id_generator),
                        location=Location(column=1, line=1),
                        name=tag_name,
                    )
                    for tag_name in self.model.tags
                ),
            ],
            table_header=TableRow(
                id=next(id_generator),
                location=Location(column=1, line=1),
                cells=[
                    *(
                        TableCell(
                            location=Location(column=1, line=1),
                            value=parameter,
                        )
                        for parameter in self.model.parameters
                    ),
                ],
            ),
        )
