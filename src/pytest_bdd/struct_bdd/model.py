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
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from pytest_bdd.compatibility.typing import Self
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.utils import deepattrgetter

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


class KeywordType(str, Enum):
    context = "Context"
    action = "Action"
    outcome = "Outcome"
    conjunction = "Conjunction"
    unknown = "Unknown"


KEYWORD_TO_TYPE: Mapping[Keyword | str | None, KeywordType] = defaultdict(
    lambda: KeywordType.unknown,
    [
        (Keyword.Given, KeywordType.context),
        (Keyword.When, KeywordType.action),
        (Keyword.Then, KeywordType.outcome),
        (Keyword.And, KeywordType.conjunction),
        (Keyword.But, KeywordType.conjunction),
        (Keyword.Star, KeywordType.unknown),
        (None, KeywordType.unknown),
    ],
)


class Node(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tags: Sequence[str] | None = Field(default_factory=cast("Callable", list), alias="Tags")
    name: str | None = Field(default=None, alias="Name")
    description: str | None = Field(default=None, alias="Description")
    comments: Sequence[str] | None = Field(default_factory=cast("Callable", list), alias="Comments")


class Table(Node):
    type: Literal["Rowed", "Columned"] | None = Field(default="Rowed", alias="Type")
    parameters: Sequence[str] | None = Field(default_factory=cast("Callable", list), alias="Parameters")
    values: Sequence[Sequence[Any]] | None = Field(default_factory=cast("Callable", list), alias="Values")

    @property
    def columned_values(self):
        values = self.values or []
        return values if self.type == "Columned" else list(zip(*values, strict=False))

    @property
    def rowed_values(self):
        values = self.values or []
        return values if self.type == "Rowed" else list(zip(*values, strict=False))


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
        default_factory=list, alias="Join"
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
            )
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
                        starmap(
                            eq,
                            product(
                                [
                                    value
                                    for _parameter, value in zip(
                                        filled_tables_parameters, filled_tables_values, strict=False
                                    )
                                    if parameter == _parameter
                                ],
                                repeat=2,
                            ),
                        )
                        for parameter in self.parameters
                    ):

                        def values_gen(current_values):
                            for parameter in self.parameters:
                                for _parameter, value in zip(filled_tables_parameters, current_values, strict=False):
                                    if parameter == _parameter:
                                        yield value
                                        break

                        yield list(values_gen(filled_tables_values))
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
        return Step(Action=value)
    if isinstance(value, dict) and len(value) == 1 and next(iter(value)) not in SubKeyword.__members__:
        return Step(Type=next(iter(value.keys())), Action=next(iter(value.values())))
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


StepKeywordType = Keyword | Annotated[str, select_step_keyword_type]


class StepPrototype(Node):
    steps: Sequence[
        Annotated[
            Annotated[Union["SubStep", "Alternative", "StepPrototype"], before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Steps")

    type: StepKeywordType | None = Field(default=Keyword.Star, alias="Type")
    data: list[Annotated[Table | Join | SubTable, convert_sub_tables_to_tables]] = Field(
        default_factory=list, alias="Data"
    )
    examples: list[Annotated[Table | Join | SubTable, convert_sub_tables_to_tables]] = Field(
        default_factory=list, alias="Examples"
    )
    keyword_type: KeywordType | None = Field(default=KeywordType.unknown)

    class Route(NamedTuple):
        tags: Sequence[str] | None
        steps: list["StepPrototype"]
        example_table: Union[Table, "Join", SubTable]

    @model_validator(mode="after")
    def set_keyword_type(self) -> Self:
        self.keyword_type = KEYWORD_TO_TYPE[self.type]
        return self

    @property
    def routes(self):
        for routes in (
            product(*map(attrgetter("routes"), self.steps))
            if self.steps
            else [[self.Route([], [], Table(Parameters=[], Values=[]))]]
        ):
            steps = [self, *chain.from_iterable(map(attrgetter("steps"), routes))]

            if self.examples:
                for _example_table in self.examples:
                    example_table = Join(Join=[*map(attrgetter("example_table"), routes), _example_table])
                    tags = list(
                        {
                            *chain.from_iterable(map(attrgetter("tags"), routes)),
                            *example_table.tags,
                            *(self.tags or ()),
                        }
                    )

                    yield self.Route(
                        tags,
                        steps,
                        example_table,
                    )
            else:
                example_table = Join(Join=[*map(attrgetter("example_table"), routes)])
                tags = list(
                    {
                        *chain.from_iterable(map(attrgetter("tags"), routes)),
                        *example_table.tags,
                        *(self.tags or ()),
                    }
                )

                yield self.Route(
                    tags,
                    steps,
                    example_table,
                )

    @classmethod
    def build_by_action(cls, action, *args, **kwargs):
        # Each subclass declares its own alias for the action field, so the
        # static signature mypy derives from Field(alias=...) cannot be used
        # here; construct dynamically instead.
        return cast("Callable[..., Any]", cls)(*args, **kwargs, action=action)

    @attrs
    class Locator(ScenarioLocatorFilterMixin):
        step: "StepPrototype" = attrib()
        filename = attrib()
        uri = attrib()
        mimetype = attrib()

        def resolve_features(self, config):
            from pytest_bdd.struct_bdd.model_builder import GherkinDocumentBuilder

            feature = GherkinDocumentBuilder(self.step).build_feature(filename=self.filename, uri=self.uri)
            yield feature, None

    def as_test(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[
                self.Locator(
                    self,
                    str(Path(filename).as_posix()),
                    str(Path(filename).relative_to(Path.cwd())),
                    mimetype=Mimetype.python,
                )
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
                )
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
    type: StepKeywordType | None = Field(default=Keyword.Star, alias="Type")
    action: str | None = Field(default=None, alias="Action")


class SubStep(BaseModel):
    sub_step: Step = Field(..., alias="Step")


class StarStep(StepPrototype):
    type: StepKeywordType = Field(default=Keyword.Star, alias="Type")
    action: str | None = Field(alias="*")


class GivenStep(StepPrototype):
    type: StepKeywordType = Field(default=Keyword.Given, alias="Type")
    action: str | None = Field(alias="Given")


class WhenStep(StepPrototype):
    type: StepKeywordType = Field(default=Keyword.When, alias="Type")
    action: str | None = Field(alias="When")


class ThenStep(StepPrototype):
    type: StepKeywordType = Field(default=Keyword.Then, alias="Type")
    action: str | None = Field(alias="Then")


class AndStep(StepPrototype):
    type: StepKeywordType = Field(default=Keyword.And, alias="Type")
    action: str | None = Field(alias="And")


class ButStep(StepPrototype):
    type: StepKeywordType = Field(default=Keyword.But, alias="Type")
    action: str | None = Field(alias="But")


Join.model_rebuild()
StepPrototype.model_rebuild()
Alternative.model_rebuild()

Given = GivenStep.build_by_action
When = WhenStep.build_by_action
Then = ThenStep.build_by_action
And = AndStep.build_by_action
But = ButStep.build_by_action
