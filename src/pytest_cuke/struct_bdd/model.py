from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from enum import Enum
from functools import partial
from inspect import getfile
from itertools import chain, product, starmap
from operator import attrgetter, eq, is_not
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal, NamedTuple, TypeGuard, cast

from attr import attrib, attrs
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from pytest_cuke.compatibility.typing import Self
from pytest_cuke.mimetypes import Mimetype
from pytest_cuke.scenario_locator import ScenarioLocatorFilterMixin
from pytest_cuke.utils import deepattrgetter

if TYPE_CHECKING:
    from pytest_cuke.model import Feature


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

    tags: Sequence[str] | None = Field(default_factory=list, alias="Tags")
    name: str | None = Field(None, alias="Name")
    description: str | None = Field(None, alias="Description")
    comments: Sequence[str] | None = Field(default_factory=list, alias="Comments")


class Table(Node):
    type: Literal["Rowed", "Columned"] | None = Field("Rowed", alias="Type")
    parameters: Sequence[str] | None = Field(default_factory=list, alias="Parameters")
    values: Sequence[Sequence[Any]] | None = Field(default_factory=list, alias="Values")

    @property
    def columned_values(self) -> Sequence[Sequence[Any]] | None:
        return (
            self.values
            if self.type == "Columned"
            else list(zip(*cast(Sequence[Sequence[Any]], self.values), strict=False))
        )

    @property
    def rowed_values(self) -> Sequence[Sequence[Any]] | None:
        return (
            self.values
            if self.type == "Rowed"
            else list(zip(*cast(Sequence[Sequence[Any]], self.values), strict=False))
        )


class SubTable(Node):
    sub_table: Table = Field(..., alias="Table")


def _convert_sub_tables_to_tables(value: Table | Join | SubTable) -> Table | Join:
    return value.sub_table if isinstance(value, SubTable) else value


convert_sub_tables_to_tables = AfterValidator(_convert_sub_tables_to_tables)


class Join(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tables: list[Annotated[Table | Join | SubTable, convert_sub_tables_to_tables]] = Field(
        default_factory=list, alias="Join"
    )

    __hash__ = id

    @property
    def tags(self) -> list[str]:
        return cast(list[str], list(dict.fromkeys(chain.from_iterable(map(attrgetter("tags"), self.tables)))))

    @property
    def name(self) -> str:
        names = cast(Iterable[str | None], chain(map(attrgetter("name"), self.tables)))
        predicate = cast(Callable[[str | None], TypeGuard[str]], partial(is_not, None))
        return "\n".join(filter(predicate, list(names)))

    @property
    def description(self) -> str:
        getter = cast("Callable[..., Callable[[Any], Iterable[str | None]]]", deepattrgetter)
        descriptions = chain.from_iterable(map(getter("description", skip_missing=True), self.tables))
        predicate = cast(Callable[[str | None], TypeGuard[str]], partial(is_not, None))
        return "\n".join(filter(predicate, descriptions))

    @property
    def comments(self) -> list[str]:
        return cast(list[str], list(chain.from_iterable(map(attrgetter("comments"), self.tables))))

    @property
    def parameters(self) -> list[str]:
        return cast(list[str], list(dict.fromkeys(chain.from_iterable(map(attrgetter("parameters"), self.tables)))))

    @property
    def type(self) -> Literal["Rowed"]:
        return "Rowed"

    @property
    def values(self) -> list[list[Any]]:
        def _() -> Iterator[list[Any]]:
            filled_tables = list(filter(attrgetter("parameters"), self.tables))
            if filled_tables:
                filled_tables_parameters = list(chain.from_iterable(map(attrgetter("parameters"), self.tables)))
                rowed_values = cast("Callable[[Any], Iterable[Sequence[Any]]]", attrgetter("rowed_values"))
                for filled_tables_values in (
                    list(chain.from_iterable(tables_values))
                    for tables_values in product(*map(rowed_values, filled_tables))
                ):
                    if all(
                        all(
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
                        )
                        for parameter in self.parameters
                    ):

                        def values_gen(current_values: Sequence[Any]) -> Iterator[Any]:
                            for parameter in self.parameters:
                                for _parameter, value in zip(filled_tables_parameters, current_values, strict=False):
                                    if parameter == _parameter:
                                        yield value
                                        break

                        yield list(values_gen(filled_tables_values))
            else:
                rowed_values = cast("Callable[[Any], Iterable[Sequence[Any]]]", attrgetter("rowed_values"))
                yield from (
                    list(chain.from_iterable(values_combination))
                    for values_combination in product(*map(rowed_values, self.tables))
                )

        return list(_())

    @property
    def columned_values(self) -> list[tuple[Any, ...]]:
        return list(zip(*self.values, strict=False))

    @property
    def rowed_values(self) -> list[list[Any]]:
        return self.values


def _before_convert_to_step(value: Any) -> Any:
    if isinstance(value, str):
        return Step(Action=value)
    if isinstance(value, dict) and len(value) == 1 and next(iter(value)) not in SubKeyword.__members__:
        return Step(Type=next(iter(value.keys())), Action=next(iter(value.values())))
    return value


before_convert_to_step = BeforeValidator(_before_convert_to_step)


def _select_step_keyword_type(value: str) -> Keyword | str:
    try:
        return Keyword(value)
    except ValueError:
        return value


select_step_keyword_type = AfterValidator(_select_step_keyword_type)


def _after_convert_sub_steps_to_steps(
    value: SubStep | StepPrototype | Alternative,
) -> Step | StepPrototype | Alternative:
    return value.sub_step if isinstance(value, SubStep) else value


after_convert_sub_steps_to_steps = AfterValidator(_after_convert_sub_steps_to_steps)


StepKeywordType = Keyword | Annotated[str, select_step_keyword_type]


class StepPrototype(Node):
    steps: Sequence[
        Annotated[
            Annotated[SubStep | Alternative | StepPrototype, before_convert_to_step],
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
        steps: list[StepPrototype]
        example_table: Table | Join | SubTable

    @model_validator(mode="after")
    def set_keyword_type(self) -> Self:
        self.keyword_type = KEYWORD_TO_TYPE[self.type]
        return self

    @property
    def routes(self) -> Iterator[StepPrototype.Route]:
        route_combinations: Iterable[tuple[StepPrototype.Route, ...]]
        if self.steps:
            route_getter = cast("Callable[[Any], Iterable[StepPrototype.Route]]", attrgetter("routes"))
            route_combinations = cast(
                "Iterable[tuple[StepPrototype.Route, ...]]",
                product(*cast("Iterable[Iterable[StepPrototype.Route]]", map(route_getter, self.steps))),
            )
        else:
            route_combinations = [(self.Route([], [], Table(parameters=[], values=[])),)]

        for routes in route_combinations:
            steps = [self, *chain.from_iterable(map(attrgetter("steps"), routes))]

            if self.examples:
                for _example_table in self.examples:
                    example_table = Join(tables=[*map(attrgetter("example_table"), routes), _example_table])
                    route_tags = cast("Callable[[Any], Iterable[str]]", attrgetter("tags"))
                    tags = list(
                        {
                            *chain.from_iterable(map(route_tags, routes)),
                            *example_table.tags,
                            *cast(Sequence[str], self.tags),
                        }
                    )

                    yield self.Route(
                        tags,
                        steps,
                        example_table,
                    )
            else:
                example_table = Join(tables=[*map(attrgetter("example_table"), routes)])
                route_tags = cast("Callable[[Any], Iterable[str]]", attrgetter("tags"))
                tags = list(
                    {
                        *chain.from_iterable(map(route_tags, routes)),
                        *example_table.tags,
                        *cast(Sequence[str], self.tags),
                    }
                )

                yield self.Route(
                    tags,
                    steps,
                    example_table,
                )

    @classmethod
    def build_by_action(cls, action: str | None, *args: Any, **kwargs: Any) -> Self:
        constructor = cast(type[Any], cls)
        return cast(Self, constructor(*args, **kwargs, action=action))

    @attrs
    class Locator(ScenarioLocatorFilterMixin):
        step: StepPrototype = attrib()
        filename: str = attrib()
        uri: str = attrib()
        mimetype: Mimetype = attrib()

        def resolve_features(self, config: Any = None, registry: Any = None) -> Iterator[Feature]:
            from pytest_cuke.struct_bdd.model_builder import GherkinDocumentBuilder

            feature = GherkinDocumentBuilder(self.step).build_feature(filename=self.filename, uri=self.uri)
            yield feature

    def as_test(self, filename: str) -> Any:
        from pytest_cuke.scenario import scenarios

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

    def as_test_decorator(self, filename: str) -> Any:
        from pytest_cuke.scenario import scenarios

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

    def __call__(self, func: Callable[..., Any]) -> Any:
        return self.as_test_decorator(getfile(func))(func)


class Alternative(Node):
    steps: Sequence[
        Annotated[
            Annotated[SubStep | Alternative | StepPrototype, before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Alternative")

    @property
    def routes(self) -> Iterator[StepPrototype.Route]:
        route_getter = cast("Callable[[Any], Iterable[StepPrototype.Route]]", attrgetter("routes"))
        yield from chain.from_iterable(map(route_getter, self.steps))


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
