from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from functools import partial
from inspect import getfile
from itertools import chain, product, starmap
from operator import attrgetter, eq, is_not
from pathlib import Path
from typing import Annotated, Any, Literal, NamedTuple, Union, cast

from attr import attrib, attrs
from cucumber_messages import Source, SourceMediaType, StepKeywordType  # type:ignore[attr-defined, import-untyped]
from pydantic import (  # type:ignore[attr-defined] # migration to pydantic 2
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

from pytest_bdd.compatibility.typing import Self
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.util.toolz_extra import deepattrgetter

# mypy: disable-error-code="typeddict-unknown-key, typeddict-item"


class Keyword(Enum):
    Given = "Given"
    When = "When"
    Then = "Then"
    And = "And"
    But = "But"
    Star = "*"


class SubKeyword(Enum):
    Step = "Step"
    Alternative = "Alternative"


KEYWORD_TO_TYPE: Mapping[Keyword | str | None, StepKeywordType] = defaultdict(
    lambda: StepKeywordType.unknown,
    [
        (Keyword.Given, StepKeywordType.context),
        (Keyword.When, StepKeywordType.action),
        (Keyword.Then, StepKeywordType.outcome),
        (Keyword.And, StepKeywordType.conjunction),
        (Keyword.But, StepKeywordType.conjunction),
        (Keyword.Star, StepKeywordType.unknown),
        (None, StepKeywordType.unknown),
    ],
)


class Node(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tags: Sequence[str] | None = Field(default_factory=cast(Callable, list), alias="Tags")
    name: str | None = Field(None, alias="Name")
    description: str | None = Field(None, alias="Description")
    comments: Sequence[str] | None = Field(default_factory=cast(Callable, list), alias="Comments")


class Table(Node):
    type: Literal["Rowed", "Columned"] | None = Field("Rowed", alias="Type")
    parameters: Sequence[str] | None = Field(default_factory=cast(Callable, list), alias="Parameters")
    values: Sequence[Sequence[Any]] | None = Field(default_factory=cast(Callable, list), alias="Values")

    @property
    def columned_values(self):
        return self.values if self.type == "Columned" else list(zip(*self.values, strict=False))

    @property
    def rowed_values(self):
        return self.values if self.type == "Rowed" else list(zip(*self.values, strict=False))


class SubTable(Node):
    sub_table: Table = Field(..., alias="Table")


@AfterValidator
def convert_sub_tables_to_tables(value):
    return value.sub_table if isinstance(value, SubTable) else value


class Join(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tables: list[Annotated[Union[Table, "Join", SubTable], convert_sub_tables_to_tables]] = Field(
        default_factory=list,
        alias="Join",
    )

    __hash__ = id

    @property
    def tags(self):
        return list(dict.fromkeys(chain.from_iterable(map(attrgetter("tags"), self.tables))))

    @property
    def name(self):
        return "\n".join(filter(partial(is_not, None), list(chain(map(attrgetter("name"), self.tables)))))

    @property
    def description(self):
        return "\n".join(
            filter(
                partial(is_not, None),
                chain.from_iterable(map(deepattrgetter("description", skip_missing=True), self.tables)),
            ),
        )

    @property
    def comments(self):
        return list(chain.from_iterable(map(attrgetter("comments"), self.tables)))

    @property
    def parameters(self):
        return list(dict.fromkeys(chain.from_iterable(map(attrgetter("parameters"), self.tables))))

    @property
    def type(self):
        return "Rowed"

    @property
    def values(self):
        def _():
            filled_tables = list(filter(attrgetter("parameters"), self.tables))
            if filled_tables:
                filled_tables_parameters = list(chain.from_iterable(map(attrgetter("parameters"), self.tables)))
                for filled_tables_values in (
                    list(chain.from_iterable(tables_values))
                    for tables_values in product(*map(attrgetter("rowed_values"), filled_tables))
                ):
                    if all(
                        all(
                            starmap(
                                eq,
                                product(
                                    [
                                        value
                                        for table_parameter, value in zip(
                                            filled_tables_parameters,
                                            filled_tables_values,
                                            strict=False,
                                        )
                                        if parameter == table_parameter
                                    ],
                                    repeat=2,
                                ),
                            ),
                        )
                        for parameter in self.parameters
                    ):

                        def values_gen(
                            parameters=self.parameters,
                            filled_tables_parameters=filled_tables_parameters,
                            filled_tables_values=filled_tables_values,
                        ):
                            for parameter in parameters:
                                for table_parameter, value in zip(
                                    filled_tables_parameters, filled_tables_values, strict=False
                                ):
                                    if parameter == table_parameter:
                                        yield value
                                        break

                        values = list(values_gen())
                        yield values
            else:
                yield from (
                    list(chain.from_iterable(values_combination))
                    for values_combination in product(*map(attrgetter("rowed_values"), self.tables))
                )

        return list(_())

    @property
    def columned_values(self):
        return list(zip(*self.values, strict=False))

    @property
    def rowed_values(self):
        return self.values


@BeforeValidator
def before_convert_to_step(value):
    if isinstance(value, str):
        return Step(action=value)
    if isinstance(value, dict) and len(value) == 1 and next(iter(value)) not in SubKeyword.__members__:
        return Step(type=next(iter(value.keys())), action=next(iter(value.values())))
    return value


@AfterValidator
def select_step_keyword_type(value):
    try:
        return Keyword(value)
    except ValueError:
        return value


@AfterValidator
def after_convert_sub_steps_to_steps(value):
    return value.sub_step if isinstance(value, SubStep) else value


StepStepKeywordType = Keyword | Annotated[str, select_step_keyword_type]


class StepPrototype(Node):
    steps: Sequence[
        Annotated[
            Annotated[Union["SubStep", "Alternative", "StepPrototype"], before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Steps")

    type: StepStepKeywordType | None = Field(default=Keyword.Star, alias="Type")
    data: list[Annotated[Table | Join | SubTable, convert_sub_tables_to_tables]] = Field(
        default_factory=list,
        alias="Data",
    )
    examples: list[Annotated[Table | Join | SubTable, convert_sub_tables_to_tables]] = Field(
        default_factory=list,
        alias="Examples",
    )
    keyword_type: StepKeywordType | None = Field(StepKeywordType.unknown)

    class Route(NamedTuple):
        tags: Sequence[str] | None
        steps: list["StepPrototype"]
        example_table: Union[Table, "Join", SubTable]

    @model_validator(mode="after")  # type: ignore[misc] # migration to pydantic 2
    def set_keyword_type(self) -> Self:
        self.keyword_type = KEYWORD_TO_TYPE[self.type]
        return self  # type: ignore[return-value] # migration to pydantic 2

    @property
    def routes(self):
        for routes in (
            product(*map(attrgetter("routes"), self.steps))
            if self.steps
            else [[self.Route([], [], Table(parameters=[], values=[]))]]
        ):
            steps = [self, *chain.from_iterable(map(attrgetter("steps"), routes))]

            if self.examples:
                for example_candidate in self.examples:
                    example_table = Join(
                        tables=[
                            *map(attrgetter("example_table"), routes),
                            example_candidate,
                        ]
                    )
                    tags = list(
                        {
                            *chain.from_iterable(map(attrgetter("tags"), routes)),
                            *example_table.tags,
                            *self.tags,
                        },
                    )

                    yield self.Route(
                        tags,
                        steps,
                        example_table,
                    )
            else:
                example_table = Join(tables=[*map(attrgetter("example_table"), routes)])
                tags = list(
                    {
                        *chain.from_iterable(map(attrgetter("tags"), routes)),
                        *example_table.tags,
                        *self.tags,
                    }
                )

                yield self.Route(
                    tags,
                    steps,
                    example_table,
                )

    @classmethod
    def build_by_action(cls, action, *args, **kwargs):
        return cls(*args, **kwargs, action=action)

    @attrs
    class Locator(ScenarioLocatorFilterMixin):
        step: "StepPrototype" = attrib()
        filename = attrib()
        uri = attrib()
        mimetype = attrib()

        def resolve_features(self, config):
            from pytest_bdd.plugin.struct_bdd.model_builder import (
                GherkinDocumentBuilder,
            )

            gherkin_document = GherkinDocumentBuilder(self.step).build_feature(
                filename=self.filename,
                uri=self.uri,
                id_generator=config.pytest_bdd_id_generator,
            )

            if isinstance(self.mimetype, SourceMediaType):
                media_type = self.mimetype
            elif isinstance(self.mimetype, Mimetype):
                media_type = self.mimetype.value
            else:
                media_type = str(self.mimetype)
            source_data = Path(self.filename).read_text(encoding="utf-8")
            try:
                feature_source = Source(
                    uri=self.uri,
                    data=source_data,
                    media_type=media_type,
                )
            except ValidationError:
                feature_source = Source(
                    uri=f"file:{Path(self.filename).as_posix()}",
                    data=source_data,
                    media_type=media_type,
                )
            yield gherkin_document, feature_source

    def as_test(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[
                self.Locator(
                    self,
                    str(Path(filename).as_posix()),
                    str(Path(filename).relative_to(Path.cwd())),
                    mimetype=Mimetype.python,
                ),
            ],
            return_test_decorator=False,
        )

    def as_test_decorator(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[
                self.Locator(
                    self,
                    str(Path(filename).as_posix()),
                    str(Path(filename).relative_to(Path.cwd())),
                    mimetype=Mimetype.python,
                ),
            ],
            return_test_decorator=True,
        )

    def __call__(self, func):
        return self.as_test_decorator(getfile(func))(func)


class Alternative(Node):
    steps: Sequence[
        Annotated[
            Annotated[Union["SubStep", "Alternative", "StepPrototype"], before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Alternative")

    @property
    def routes(self):
        yield from chain.from_iterable(map(attrgetter("routes"), self.steps))


class Step(StepPrototype):
    type: StepStepKeywordType | None = Field(default=Keyword.Star, alias="Type")
    action: str | None = Field(None, alias="Action")


class SubStep(BaseModel):
    sub_step: Step = Field(..., alias="Step")


class StarStep(StepPrototype):
    type: StepStepKeywordType = Field(Keyword.Star, alias="Type")
    action: str | None = Field(alias=Keyword.Star.value)


class GivenStep(StepPrototype):
    type: StepStepKeywordType = Field(Keyword.Given, alias="Type")
    action: str | None = Field(alias=Keyword.Given.value)


class WhenStep(StepPrototype):
    type: StepStepKeywordType = Field(Keyword.When, alias="Type")
    action: str | None = Field(alias=Keyword.When.value)


class ThenStep(StepPrototype):
    type: StepStepKeywordType = Field(Keyword.Then, alias="Type")
    action: str | None = Field(alias=Keyword.Then.value)


class AndStep(StepPrototype):
    type: StepStepKeywordType = Field(Keyword.And, alias="Type")
    action: str | None = Field(alias=Keyword.And.value)


class ButStep(StepPrototype):
    type: StepStepKeywordType = Field(Keyword.But, alias="Type")
    action: str | None = Field(alias=Keyword.But.value)


Join.model_rebuild()  # type:ignore[attr-defined] # migration to pydantic 2
StepPrototype.model_rebuild()  # type:ignore[attr-defined] # migration to pydantic 2
Alternative.model_rebuild()  # type:ignore[attr-defined] # migration to pydantic 2

Given = GivenStep.build_by_action
When = WhenStep.build_by_action
Then = ThenStep.build_by_action
And = AndStep.build_by_action
But = ButStep.build_by_action
