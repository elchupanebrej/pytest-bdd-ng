"""
Step model classes for struct BDD.

Responsibility:
    Step model classes for struct BDD. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - before_convert_to_step: owns nested behavior below this boundary
    - select_step_keyword_type: owns nested behavior below this boundary
    - after_convert_sub_steps_to_steps: owns nested behavior below this boundary
    - StepPrototype: owns nested behavior below this boundary
    - Alternative: owns nested behavior below this boundary
    - Step: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `_steps`

State and side effects:
    mutates type, action, steps, tags, example_table; depends on builtins, collections.abc.Callable,
    collections.abc.Iterator, collections.abc.Sequence, inspect.getfile.

Invariants:
    - `pytest_bdd.plugin.struct_bdd.model._steps` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
"""

import builtins
from collections.abc import Callable, Iterator, Sequence
from inspect import getfile
from itertools import chain, product
from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, NamedTuple, Union, cast

from attrs import define, field
from cucumber_messages import (
    Source,
    SourceMediaType,
    StepKeywordType,
)
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    ValidationError,
    model_validator,
)

from pytest_bdd.compatibility.typing import Self
from pytest_bdd.mimetype import Mimetype
from pytest_bdd.plugin.struct_bdd.model._base import (
    KEYWORD_TO_TYPE,
    Join,
    Keyword,
    Node,
    StepPrototypeT,
    SubKeyword,
    SubTable,
    Table,
    TableNode,
    convert_sub_tables_to_tables,
)
from pytest_bdd.scenario import scenarios
from pytest_bdd.scenario_locator import ScenarioLocatorFilterMixin
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from pytest_bdd.compatibility.parser import ParsedFeature
    from pytest_bdd.compatibility.pytest import Config
    from pytest_bdd.scenario import ScenarioDecorator, ScenarioTest
    from pytest_bdd.types.protocol import HasPytestStash

# mypy: disable-error-code="typeddict-unknown-key, typeddict-item"


@BeforeValidator
def before_convert_to_step(value: object) -> object:
    """
    Convert value to Step before validation.

    Args:
        value: Input value (string or dict).

    Returns:
        Step object or original value.

    Responsibility:
        Convert value to Step before validation. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.before_convert_to_step`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - next: collaborator call used by this boundary
        - iter: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - Step: collaborator call used by this boundary
        - cast: collaborator call used by this boundary
        - len: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `before_convert_to_step`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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

    Responsibility:
        Select step keyword type from string. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.select_step_keyword_type`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Keyword: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `select_step_keyword_type`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

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

    Responsibility:
        Convert SubStep to Step after validation. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.struct_bdd.model._steps.after_convert_sub_steps_to_steps` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `after_convert_sub_steps_to_steps`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3

    """
    return value.sub_step if isinstance(value, SubStep) else value


StepStepKeywordType = Keyword | Annotated[str, select_step_keyword_type]


class StepPrototype(Node):
    """
    Represent step prototype state.

    Yields:
        Generated values.

    Responsibility:
        Represent step prototype state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Route: owns nested behavior below this boundary
        - set_keyword_type: owns nested behavior below this boundary
        - routes: owns nested behavior below this boundary
        - build_by_action: owns nested behavior below this boundary
        - Locator: owns nested behavior below this boundary
        - as_test: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `StepPrototype`
        - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `StepPrototype`
        - src/pytest_bdd/plugin/struct_bdd/plugin.py: imports or references `StepPrototype`

    State and side effects:
        mutates steps, tags, example_table, media_type, feature_source; depends on
        pytest_bdd.compatibility.parser.ParsedFeature,
        pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

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
        """
        Step route with inherited tags, steps, and example table.

        Responsibility:
            Step route with inherited tags, steps, and example table. It directly owns the observable contract, local
            decisions, and maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.Route`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - None, leaf-level implementation boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Route`

        State and side effects:
            mutates tags, steps, example_table.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.Route` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=2
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=2
            #arch-eval:locational_stability=3
        """

        tags: Sequence[str] | None
        steps: list["StepPrototype"]
        example_table: TableNode

    @model_validator(mode="after")
    def set_keyword_type(self) -> Self:
        """
        Set keyword type based on step type.

        Returns:
            Self with keyword_type set.

        Responsibility:
            Set keyword type based on step type. It directly owns the observable contract, local decisions, and
            maintenance boundary for this method. That boundary is intentionally stated in prose so maintainers can
            distinguish owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.set_keyword_type` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - model_validator: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `set_keyword_type`

        State and side effects:
            mutates self.keyword_type.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.set_keyword_type` keeps its documented import
              path, ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        self.keyword_type = KEYWORD_TO_TYPE[self.type]
        return self

    @property
    def routes(self) -> Iterator[Route]:
        """
        Handle routes.

        Yields:
            Generated values.

        Responsibility:
            Handle routes. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.routes`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - map: collaborator call used by this boundary
            - attrgetter: collaborator call used by this boundary
            - self.Route: collaborator call used by this boundary
            - list: collaborator call used by this boundary
            - chain.from_iterable: collaborator call used by this boundary
            - Join: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `routes`
            - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `routes`

        State and side effects:
            mutates example_table, tags, routes, steps.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.routes` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Build step prototype by action. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.build_by_action` because it keeps the nearest code,
            data shape, call signature, and failure knowledge together.

        Delegates:
            - cast: collaborator call used by this boundary
            - cls: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `build_by_action`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        return cast("StepPrototypeT", cls(*args, **kwargs, action=action))  # type: ignore[redundant-cast, call-arg]  # dynamic Step class construction

    @define
    class Locator(ScenarioLocatorFilterMixin):
        """
        Scenario locator for a struct BDD step prototype.

        Responsibility:
            Scenario locator for a struct BDD step prototype. It directly owns the observable contract, local decisions,
            and maintenance boundary for this class.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.Locator`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - resolve_features: owns nested behavior below this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Locator`

        State and side effects:
            mutates media_type, feature_source, step, filename, uri; depends on
            pytest_bdd.compatibility.parser.ParsedFeature,
            pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.

        Invariants:
            - `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.Locator` keeps its documented import path,
              ownership boundary, and observable behavior stable for callers.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=3
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=4
            #arch-eval:entity_fullness=3
            #arch-eval:locational_stability=3
        """

        step: "StepPrototype" = field()
        filename: str = field()
        uri: str = field()
        mimetype: SourceMediaType | Mimetype | str = field()

        def resolve_features(
            self,
            config: "Config | HasPytestStash",
        ) -> Iterator["tuple[ParsedFeature, Source]"]:
            """
            Resolve features.

            Yields:
                Generated values.

            Responsibility:
                Resolve features. It directly owns the observable contract, local decisions, and maintenance boundary
                for this method. That boundary is intentionally stated in prose so maintainers can distinguish owned
                work from collaborators before editing.

            Reason for existence:
                This entity is the information expert for
                `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.Locator.resolve_features` because it keeps the
                nearest code, data shape, call signature, and failure knowledge together.

            Delegates:
                - isinstance: collaborator call used by this boundary
                - Path: collaborator call used by this boundary
                - Source: collaborator call used by this boundary
                - GherkinDocumentBuilder.build_feature: collaborator call used by this boundary
                - GherkinDocumentBuilder: collaborator call used by this boundary
                - IdGenerator.from_stash: collaborator call used by this boundary

            Cohesion:
                The implementation stays together because its imports, calls, state writes, and return contract describe
                one maintainable decision unit.

            Separation:
                - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and
                  changeable without widening caller knowledge.

            Main consumers:
                - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `resolve_features`
                - src/pytest_bdd/scenario_locator/base.py: imports or references `resolve_features`

            State and side effects:
                mutates media_type, feature_source, gherkin_document, source_data; depends on
                pytest_bdd.compatibility.parser.ParsedFeature,
                pytest_bdd.plugin.struct_bdd.model_builder.GherkinDocumentBuilder.

            Invariants:
                - `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.Locator.resolve_features` keeps its
                  documented import path, ownership boundary, and observable behavior stable for callers.

            Architecture score:
                #arch-eval:reason_for_existence=4
                #arch-eval:owned_responsibility=4
                #arch-eval:delegation_boundary=4
                #arch-eval:cohesion=4
                #arch-eval:separation=3
                #arch-eval:consumer_clarity=4
                #arch-eval:state_invariants=4
                #arch-eval:entity_fullness=4
                #arch-eval:locational_stability=3

            """
            from pytest_bdd.compatibility.parser import ParsedFeature  # noqa: PLC0415
            from pytest_bdd.plugin.struct_bdd.model_builder import (  # noqa: PLC0415 -- circular import with model_builder.py, resolved via lazy load
                GherkinDocumentBuilder,
            )

            gherkin_document = GherkinDocumentBuilder(self.step).build_feature(
                filename=self.filename,
                uri=self.uri,
                id_generator=IdGenerator.from_stash(config.stash),
            )

            if isinstance(self.mimetype, SourceMediaType):
                media_type: Any = self.mimetype
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
            yield (
                ParsedFeature(
                    gherkin_document=gherkin_document,
                    filename=self.filename,
                    raw_data=source_data,
                ),
                feature_source,
            )

    def as_test(self, filename: str | Path) -> "ScenarioTest":
        """
        Convert struct BDD model to pytest scenario test.

        Returns:
            Scenario test function.

        Responsibility:
            Convert struct BDD model to pytest scenario test. It directly owns the observable contract, local decisions,
            and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.as_test`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - scenarios: collaborator call used by this boundary
            - self.Locator: collaborator call used by this boundary
            - Path.as_posix: collaborator call used by this boundary
            - Path.relative_to: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `as_test`
            - src/pytest_bdd/plugin/struct_bdd/plugin.py: imports or references `as_test`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Convert struct BDD model to pytest scenario decorator. It directly owns the observable contract, local
            decisions, and maintenance boundary for this method.

        Reason for existence:
            This entity is the information expert for
            `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.as_test_decorator` because it keeps the nearest
            code, data shape, call signature, and failure knowledge together.

        Delegates:
            - str: collaborator call used by this boundary
            - Path: collaborator call used by this boundary
            - scenarios: collaborator call used by this boundary
            - self.Locator: collaborator call used by this boundary
            - Path.as_posix: collaborator call used by this boundary
            - Path.relative_to: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `as_test_decorator`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

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

        Responsibility:
            Apply decorator to function. It directly owns the observable contract, local decisions, and maintenance
            boundary for this method. That boundary is intentionally stated in prose so maintainers can distinguish
            owned work from collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StepPrototype.__call__`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - self.as_test_decorator: collaborator call used by this boundary
            - getfile: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `__call__`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        return self.as_test_decorator(getfile(func))(func)


class Alternative(Node):
    """
    Represent alternative state.

    Yields:
        Generated values.

    Responsibility:
        Represent alternative state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.Alternative` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - routes: owns nested behavior below this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/_base.py: imports or references `Alternative`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Alternative`

    State and side effects:
        mutates steps.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.Alternative` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3

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

        Responsibility:
            Handle routes. It directly owns the observable contract, local decisions, and maintenance boundary for this
            method. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
            collaborators before editing.

        Reason for existence:
            This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.Alternative.routes`
            because it keeps the nearest code, data shape, call signature, and failure knowledge together.

        Delegates:
            - chain.from_iterable: collaborator call used by this boundary
            - map: collaborator call used by this boundary
            - attrgetter: collaborator call used by this boundary

        Cohesion:
            The implementation stays together because its imports, calls, state writes, and return contract describe one
            maintainable decision unit.

        Separation:
            - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
              without widening caller knowledge.

        Main consumers:
            - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `routes`
            - src/pytest_bdd/plugin/struct_bdd/model_builder.py: imports or references `routes`

        State and side effects:
            keeps no local persistent state beyond call-local values.

        Architecture score:
            #arch-eval:reason_for_existence=4
            #arch-eval:owned_responsibility=4
            #arch-eval:delegation_boundary=4
            #arch-eval:cohesion=4
            #arch-eval:separation=3
            #arch-eval:consumer_clarity=4
            #arch-eval:state_invariants=3
            #arch-eval:entity_fullness=4
            #arch-eval:locational_stability=3

        """
        yield from chain.from_iterable(map(attrgetter("routes"), self.steps))


class Step(StepPrototype):
    """
    Represent step state.

    Responsibility:
        Represent step state. It directly owns the observable contract, local decisions, and maintenance boundary for
        this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.Step` because it keeps the
        nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/feature_binding.py: imports or references `Step`
        - src/pytest_bdd/plugin/pickle_runner/entrypoint.py: imports or references `Step`
        - src/pytest_bdd/plugin/pickle_runner/hook.py: imports or references `Step`
        - src/pytest_bdd/plugin/struct_bdd/model/_base.py: imports or references `Step`
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `Step`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.Step` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    type: StepStepKeywordType | None = Field(default=Keyword.Star, alias="Type")
    action: str | None = Field(None, alias="Action")


class SubStep(BaseModel):
    """
    Represent sub step state.

    Responsibility:
        Represent sub step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.SubStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `SubStep`

    State and side effects:
        mutates sub_step.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.SubStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    sub_step: Step = Field(..., alias="Step")


class StarStep(StepPrototype):
    """
    Represent star step state.

    Responsibility:
        Represent star step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.StarStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `StarStep`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.StarStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    type: StepStepKeywordType = Field(Keyword.Star, alias="Type")
    action: str | None = Field(alias=Keyword.Star.value)


class GivenStep(StepPrototype):
    """
    Represent given step state.

    Responsibility:
        Represent given step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.GivenStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `GivenStep`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.GivenStep` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    type: StepStepKeywordType = Field(Keyword.Given, alias="Type")
    action: str | None = Field(alias=Keyword.Given.value)


class WhenStep(StepPrototype):
    """
    Represent when step state.

    Responsibility:
        Represent when step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.WhenStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `WhenStep`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.WhenStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    type: StepStepKeywordType = Field(Keyword.When, alias="Type")
    action: str | None = Field(alias=Keyword.When.value)


class ThenStep(StepPrototype):
    """
    Represent then step state.

    Responsibility:
        Represent then step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.ThenStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `ThenStep`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.ThenStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    type: StepStepKeywordType = Field(Keyword.Then, alias="Type")
    action: str | None = Field(alias=Keyword.Then.value)


class AndStep(StepPrototype):
    """
    Represent and step state.

    Responsibility:
        Represent and step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.AndStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `AndStep`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.AndStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    type: StepStepKeywordType = Field(Keyword.And, alias="Type")
    action: str | None = Field(alias=Keyword.And.value)


class ButStep(StepPrototype):
    """
    Represent but step state.

    Responsibility:
        Represent but step state. It directly owns the observable contract, local decisions, and maintenance boundary
        for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.struct_bdd.model._steps.ButStep` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Field: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/struct_bdd/model/facade.py: imports or references `ButStep`

    State and side effects:
        mutates type, action.

    Invariants:
        - `pytest_bdd.plugin.struct_bdd.model._steps.ButStep` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    type: StepStepKeywordType = Field(Keyword.But, alias="Type")
    action: str | None = Field(alias=Keyword.But.value)


StepPrototype.model_rebuild()
Alternative.model_rebuild()

Given = GivenStep.build_by_action
When = WhenStep.build_by_action
Then = ThenStep.build_by_action
And = AndStep.build_by_action
But = ButStep.build_by_action
