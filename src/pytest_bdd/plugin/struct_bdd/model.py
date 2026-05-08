"""Provide model helpers."""

import builtins
from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from enum import Enum
from inspect import getfile
from itertools import chain, product, starmap
from operator import attrgetter, eq
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, NamedTuple, TypeAlias, TypeVar, Union, cast

from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    GherkinDocument,
    Source,
    SourceMediaType,
    StepKeywordType,
)
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
from pytest_bdd.scenario import scenarios
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import deepattrgetter

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.scenario import ScenarioDecorator, ScenarioTest
    from pytest_bdd.types.protocol import HasPytestStash

# mypy: disable-error-code="typeddict-unknown-key, typeddict-item"


class Keyword(Enum):
    """Represent keyword state."""

    Given = "Given"
    When = "When"
    Then = "Then"
    And = "And"
    But = "But"
    Star = "*"


class SubKeyword(Enum):
    """Represent sub keyword state."""

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
    """Represent node state."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    tags: Sequence[str] | None = Field(default_factory=cast("Callable", list), alias="Tags")
    name: str | None = Field(None, alias="Name")
    description: str | None = Field(None, alias="Description")
    comments: Sequence[str] | None = Field(default_factory=cast("Callable", list), alias="Comments")


class Table(Node):
    """Represent table state."""

    type: Literal["Rowed", "Columned"] | None = Field("Rowed", alias="Type")
    parameters: Sequence[str] | None = Field(default_factory=cast("Callable", list), alias="Parameters")
    values: Sequence[Sequence[object]] | None = Field(default_factory=cast("Callable", list), alias="Values")

    @property
    def columned_values(self) -> Sequence[Sequence[object]]:
        """Handle columned values."""
        values = self.values or []
        return values if self.type == "Columned" else list(zip(*values, strict=False))

    @property
    def rowed_values(self) -> Sequence[Sequence[object]]:
        """Handle rowed values."""
        values = self.values or []
        return values if self.type == "Rowed" else list(zip(*values, strict=False))


class SubTable(Node):
    """Represent sub table state."""

    sub_table: Table = Field(..., alias="Table")


@AfterValidator
def convert_sub_tables_to_tables(value: object) -> object:
    """
    Convert sub tables to tables.

    Args:
        value: Input value that may be a SubTable.

    Returns:
        SubTable converted to Table, or original value.

    """
    return value.sub_table if isinstance(value, SubTable) else value


class Join(BaseModel):
    """
    Represent join state.

    Yields:
        Generated values.

    """

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
    def tags(self) -> list[str]:
        """Handle tags."""
        return list(dict.fromkeys(chain.from_iterable(table.tags or [] for table in self._tables())))

    @property
    def name(self) -> str:
        """Handle name."""
        return "\n".join(table.name for table in self._tables() if table.name is not None)

    @property
    def description(self) -> str:
        """Handle description."""
        descriptions = chain.from_iterable(map(deepattrgetter("description", skip_missing=True), self.tables))
        return "\n".join(str(description) for description in descriptions if description is not None)

    @property
    def comments(self) -> list[str]:
        """Handle comments."""
        return list(chain.from_iterable(table.comments or [] for table in self._tables()))

    @property
    def parameters(self) -> list[str]:
        """Handle parameters."""
        return list(dict.fromkeys(chain.from_iterable(table.parameters or [] for table in self._tables())))

    @property
    def type(self) -> Literal["Rowed"]:
        """Handle type."""
        return "Rowed"

    @property
    def values(self) -> list[list[object]]:
        """Return rows with parameterized table values expanded."""

        def _() -> Iterator[list[object]]:
            filled_tables = list(filter(attrgetter("parameters"), self.tables))
            if filled_tables:
                filled_tables_parameters = list(
                    chain.from_iterable(table.parameters or [] for table in self._tables()),
                )
                for filled_tables_values in (
                    list(chain.from_iterable(tables_values))
                    for tables_values in product(*map(attrgetter("rowed_values"), map(self._table, filled_tables)))
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
                            parameters: Sequence[str] = self.parameters,
                            filled_tables_parameters: Sequence[str] = filled_tables_parameters,
                            filled_tables_values: Sequence[object] = filled_tables_values,
                        ) -> Iterator[object]:
                            for parameter in parameters:
                                for table_parameter, value in zip(
                                    filled_tables_parameters,
                                    filled_tables_values,
                                    strict=False,
                                ):
                                    if parameter == table_parameter:
                                        yield value
                                        break

                        yield list(values_gen())
            else:
                yield from (
                    list(chain.from_iterable(values_combination))
                    for values_combination in product(*map(attrgetter("rowed_values"), self._tables()))
                )

        return list(_())

    @staticmethod
    def _table(table: Union[Table, "Join", SubTable]) -> Union[Table, "Join"]:
        return table.sub_table if isinstance(table, SubTable) else table

    def _tables(self) -> Iterator[Union[Table, "Join"]]:
        return map(self._table, self.tables)

    @property
    def columned_values(self) -> list[tuple[object, ...]]:
        """Handle columned values."""
        return list(zip(*self.values, strict=False))

    @property
    def rowed_values(self) -> list[list[object]]:
        """Handle rowed values."""
        return cast("list[list[object]]", self.values)


TableNode: TypeAlias = Table | Join
StepPrototypeT = TypeVar("StepPrototypeT", bound="StepPrototype")


@BeforeValidator
def before_convert_to_step(value: object) -> object:
    """
    Convert value to Step before validation.

    Args:
        value: Input value (string or dict).

    Returns:
        Step object or original value.

    """
    if isinstance(value, str):
        return Step(action=value)
    if isinstance(value, dict) and len(value) == 1 and next(iter(value)) not in SubKeyword.__members__:
        return Step(
            type=cast("StepStepKeywordType | None", next(iter(value.keys()))),
            action=cast("str | None", next(iter(value.values()))),
        )
    return value


@AfterValidator
def select_step_keyword_type(value: str) -> Keyword | str:
    """
    Select step keyword type from string.

    Args:
        value: Keyword string.

    Returns:
        Keyword enum or original string.

    """
    try:
        return Keyword(value)
    except ValueError:
        return value


@AfterValidator
def after_convert_sub_steps_to_steps(value: object) -> object:
    """
    Convert SubStep to Step after validation.

    Args:
        value: Input value that may be a SubStep.

    Returns:
        SubStep converted to Step, or original value.

    """
    return value.sub_step if isinstance(value, SubStep) else value


StepStepKeywordType = Keyword | Annotated[str, select_step_keyword_type]


class StepPrototype(Node):
    """
    Represent step prototype state.

    Yields:
        Generated values.

    """

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
        """Step route with inherited tags, steps, and example table."""

        tags: Sequence[str] | None
        steps: list["StepPrototype"]
        example_table: TableNode

    @model_validator(mode="after")  # type: ignore[misc] # migration to pydantic 2
    def set_keyword_type(self) -> Self:
        """
        Set keyword type based on step type.

        Returns:
            Self with keyword_type set.

        """
        self.keyword_type = KEYWORD_TO_TYPE[self.type]
        return self  # type: ignore[return-value] # migration to pydantic 2

    @property
    def routes(self) -> Iterator[Route]:
        """
        Handle routes.

        Yields:
            Generated values.

        """
        for route_items in (
            product(*map(attrgetter("routes"), self.steps))
            if self.steps
            else [[self.Route([], [], Table(parameters=[], values=[]))]]
        ):
            routes = list(cast("Sequence[StepPrototype.Route]", route_items))
            steps = [self, *chain.from_iterable(map(attrgetter("steps"), routes))]

            if self.examples:
                for example_candidate in self.examples:
                    example_table = Join(
                        tables=[
                            *map(attrgetter("example_table"), routes),
                            example_candidate,
                        ],
                    )
                    tags = list(
                        {
                            *chain.from_iterable(route.tags or [] for route in routes),
                            *example_table.tags,
                            *(self.tags or []),
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
                        *chain.from_iterable(route.tags or [] for route in routes),
                        *example_table.tags,
                        *(self.tags or []),
                    },
                )

                yield self.Route(
                    tags,
                    steps,
                    example_table,
                )

    @classmethod
    def build_by_action(
        cls: builtins.type[StepPrototypeT],
        action: str | None,
        *args: object,
        **kwargs: object,
    ) -> StepPrototypeT:
        """
        Build step prototype by action.

        Returns:
            Step prototype instance.

        """
        return cast("StepPrototypeT", cls(*args, **kwargs, action=action))  # type: ignore[call-arg]

    @define
    class Locator(ScenarioLocatorFilterMixin):
        """Scenario locator for a struct BDD step prototype."""

        step: "StepPrototype" = field()
        filename: str = field()
        uri: str = field()
        mimetype: SourceMediaType | Mimetype | str = field()

        def resolve_features(
            self,
            config: "Config | HasPytestStash",
        ) -> Iterator[tuple[GherkinDocument, Source]]:
            """
            Resolve features.

            Yields:
                Generated values.

            """
            from pytest_bdd.plugin.struct_bdd.model_builder import (  # noqa: PLC0415 -- circular import with model_builder.py, resolved via lazy load
                GherkinDocumentBuilder,
            )

            gherkin_document = GherkinDocumentBuilder(self.step).build_feature(
                filename=self.filename,
                uri=self.uri,
                id_generator=IdGenerator.from_stash(config.stash),
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

    def as_test(self, filename: str | Path) -> "ScenarioTest":
        """
        Convert struct BDD model to pytest scenario test.

        Returns:
            Scenario test function.

        """
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

    def as_test_decorator(self, filename: str | Path) -> "ScenarioDecorator":
        """
        Convert struct BDD model to pytest scenario decorator.

        Returns:
            Scenario decorator.

        """
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

    def __call__(self, func: Callable[..., object]) -> Callable[..., object]:
        """
        Apply decorator to function.

        Returns:
            Decorated function.

        """
        return self.as_test_decorator(getfile(func))(func)


class Alternative(Node):
    """
    Represent alternative state.

    Yields:
        Generated values.

    """

    steps: Sequence[
        Annotated[
            Annotated[Union["SubStep", "Alternative", "StepPrototype"], before_convert_to_step],
            after_convert_sub_steps_to_steps,
        ]
    ] = Field(default_factory=list, alias="Alternative")

    @property
    def routes(self) -> Iterator[StepPrototype.Route]:
        """
        Handle routes.

        Yields:
            Generated values.

        """
        yield from chain.from_iterable(map(attrgetter("routes"), self.steps))


class Step(StepPrototype):
    """Represent step state."""

    type: StepStepKeywordType | None = Field(default=Keyword.Star, alias="Type")
    action: str | None = Field(None, alias="Action")


class SubStep(BaseModel):
    """Represent sub step state."""

    sub_step: Step = Field(..., alias="Step")


class StarStep(StepPrototype):
    """Represent star step state."""

    type: StepStepKeywordType = Field(Keyword.Star, alias="Type")
    action: str | None = Field(alias=Keyword.Star.value)


class GivenStep(StepPrototype):
    """Represent given step state."""

    type: StepStepKeywordType = Field(Keyword.Given, alias="Type")
    action: str | None = Field(alias=Keyword.Given.value)


class WhenStep(StepPrototype):
    """Represent when step state."""

    type: StepStepKeywordType = Field(Keyword.When, alias="Type")
    action: str | None = Field(alias=Keyword.When.value)


class ThenStep(StepPrototype):
    """Represent then step state."""

    type: StepStepKeywordType = Field(Keyword.Then, alias="Type")
    action: str | None = Field(alias=Keyword.Then.value)


class AndStep(StepPrototype):
    """Represent and step state."""

    type: StepStepKeywordType = Field(Keyword.And, alias="Type")
    action: str | None = Field(alias=Keyword.And.value)


class ButStep(StepPrototype):
    """Represent but step state."""

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
