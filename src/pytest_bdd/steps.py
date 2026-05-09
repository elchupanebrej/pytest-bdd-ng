"""
Step decorators.

Example:
@given("I have an article", target_fixture="article")
def given_article(author):
    return create_test_article(author=author)


@when("I go to the article page")
def go_to_the_article_page(browser, article):
    browser.visit(urljoin(browser.url, "/articles/{0}/".format(article.id)))


@then("I should not see the error message")
def no_error_message(browser):
    with pytest.raises(ElementDoesNotExist):
        browser.find_by_css(".message.error").first


Multiple names for the steps:

@given("I have an article")
@given("there is an article")
def article(author):
    return create_test_article(author=author)


Reusing existing fixtures for a different step name:


@given("I have a beautiful article")
def given_beautiful_article(article):
    pass

"""

import warnings
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from contextlib import suppress
from inspect import getfile, getsourcelines
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, cast
from uuid import uuid4
from warnings import warn

import pytest
from _pytest.fixtures import FixtureRequest
from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]
    Feature,
    JavaMethod,
    JavaStackTraceElement,
    Location,
    Pickle,
    PickleStepType,
    SourceReference,
    StepDefinition,
    StepDefinitionPattern,
)
from cucumber_messages import PickleStep as Step  # type:ignore[attr-defined]
from ordered_set import OrderedSet
from typing_extensions import Protocol, runtime_checkable

from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.pytest import Config, FixtureLookupError, get_config_root_path
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers import StepParser
from pytest_bdd.plugin.pickle_runner.const import Steps
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning
from pytest_bdd.util.inspect_extra import get_caller_module_locals
from pytest_bdd.util.other import IdGenerator, format_as_python_identifier
from pytest_bdd.util.toolz_extra import getitemdefault, setdefaultattr

if TYPE_CHECKING:
    from types import FunctionType


class StepFunc(Protocol):
    """Represent step func state."""

    __name__: str


StepDecorator: TypeAlias = Callable[[StepFunc], StepFunc]
ConverterT: TypeAlias = Callable[[object], object]
ParamsFixturesMapping: TypeAlias = bool | Collection[str] | Mapping[object, str | None]


def _resolve_callable_source_location(func: StepFunc) -> tuple[str, int]:
    typed_func = cast("FunctionType", func)
    source_file = getfile(typed_func)
    try:
        source_line = getsourcelines(typed_func)[1]
    except (OSError, TypeError):
        source_line = getattr(getattr(func, "__code__", None), "co_firstlineno", 1) or 1
    return source_file, int(source_line)


def given(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Given step decorator.

    :param parserlike: Step name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.

    Returns:
        Step decorator function.

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.context,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def when(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    When step decorator.

    :param parserlike: Step name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.

    Returns:
        Step decorator function.

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.action,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def then(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Then step decorator.

    :param parserlike: Step name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.

    Returns:
        Step decorator function.

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.outcome,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


def step(  # noqa: PLR0913, PLR0917
    parserlike: object,
    anonymous_group_names: Iterable[str] | None = None,
    converters: Mapping[str, ConverterT] | None = None,
    target_fixture: str | None = None,
    target_fixtures: Sequence[str] | None = None,
    params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa: FBT002
    param_defaults: Mapping[str, object] | None = None,
    *,
    liberal: bool | None = None,
    stacklevel: int = 1,
) -> StepDecorator:
    """
    Liberal step decorator which could be used with any keyword.

    :param parserlike: Step name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: Step parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.

    Returns:
        Step decorator function.

    """
    return StepDefinitionManager.decorator_builder(
        PickleStepType.unknown,
        parserlike,
        anonymous_group_names=anonymous_group_names,
        converters=converters,
        target_fixture=target_fixture,
        target_fixtures=target_fixtures,
        params_fixtures_mapping=params_fixtures_mapping,
        param_defaults=param_defaults,
        liberal=liberal,
        stacklevel=stacklevel + 1,
    )


class StepDefinitionManager:
    """
    Represent step definition manager state.

    Yields:
        Generated values.

    Raises:
        MatchNotFoundError: If the operation cannot be completed.
        TypeError: If the operation cannot be completed.

    """

    Model: "TypeAlias" = "Step"

    @define
    class Matcher:
        """Match scenario steps to registered step definitions."""

        config: Config = field()
        request: FixtureRequest = field(init=False)
        feature: Feature = field(init=False)
        pickle: Pickle = field(init=False)
        step: Step = field(init=False)
        previous_step: Step | None = field(init=False)
        step_registry: "StepDefinitionManager.Registry" = field(init=False)
        step_type_context: PickleStepType | None = field(default=None)

        class MatchNotFoundError(RuntimeError):
            """Raised when no step definition matches a scenario step."""

        def __call__(  # noqa: PLR0913, PLR0917
            self,
            request: FixtureRequest,
            feature: Feature,
            pickle: Pickle,
            step: Step,
            previous_step: Step | None,
            step_registry: "StepDefinitionManager.Registry",
        ) -> "StepDefinitionManager.Definition":
            """
            Match a runtime step to this definition.

            Returns:
                Matched step definition.

            """
            self.request = request
            self.feature = feature
            self.pickle = pickle
            self.step = step
            self.previous_step = previous_step
            self.step_registry = step_registry

            self.step_type_context = (
                self.step_type_context
                if self.step.type is PickleStepType.unknown and self.step_type_context is not None
                else self.step.type
            )

            step_definitions = list(
                self.find_step_definition_matches(
                    self.step_registry,
                    (
                        self.strict_matcher,
                        self.unspecified_matcher,
                        self.liberal_matcher,
                    ),
                ),
            )

            if len(step_definitions) > 0:
                if len(step_definitions) > 1:
                    warn(
                        PytestBDDStepDefinitionWarning(f"Alternative step definitions are found: {step_definitions}"),
                        stacklevel=2,
                    )
                return step_definitions[0]
            raise self.MatchNotFoundError(self.step.text)

        def strict_matcher(self, step_definition: "StepDefinitionManager.Definition") -> bool:
            """
            Check if step definition strictly matches.

            Returns:
                True if step definition matches strictly.

            """
            return step_definition.type_ == self.step_type_context and step_definition.parser.is_matching(
                self.request,
                self.step.text,
            )

        def unspecified_matcher(self, step_definition: "StepDefinitionManager.Definition") -> bool:
            """
            Check if step definition matches with unspecified type.

            Returns:
                True if matches with unspecified type.

            """
            return (
                PickleStepType.unknown in {self.step_type_context, step_definition.type_}
            ) and step_definition.parser.is_matching(
                self.request,
                self.step.text,
            )

        def liberal_matcher(self, step_definition: "StepDefinitionManager.Definition") -> bool:
            """
            Check if step definition matches using liberal matching.

            Returns:
                True if liberal matching applies, False otherwise.

            """
            if step_definition.liberal is None:
                if self.config.option.liberal_steps is None:
                    is_step_definition_liberal = self.config.getini(str(Steps.Ini.LIBERAL_OPTION))
                else:
                    is_step_definition_liberal = getattr(self.config.option, str(Steps.Cli.LIBERAL_OPTION), False)
            else:
                is_step_definition_liberal = step_definition.liberal

            return all(
                (
                    not self.unspecified_matcher(step_definition),
                    is_step_definition_liberal,
                    step_definition.type_ != self.step_type_context,
                    step_definition.parser.is_matching(self.request, self.step.text),
                ),
            )

        @staticmethod
        def find_step_definition_matches(
            registry: "StepDefinitionManager.Registry | None",
            matchers: Sequence[Callable[["StepDefinitionManager.Definition"], bool]],
        ) -> Iterator["StepDefinitionManager.Definition"]:
            """
            Find step definition matches.

            Yields:
                Generated values.

            """
            if registry:
                found_matches = False
                for matcher in matchers:
                    for step_definition in registry:
                        if matcher(step_definition):
                            found_matches = True
                            yield step_definition
                    if found_matches:
                        break
                if not found_matches:
                    with suppress(AttributeError):
                        yield from StepDefinitionManager.Matcher.find_step_definition_matches(registry.parent, matchers)

    @define(eq=False)
    class Definition:
        """Registered step definition."""

        func: StepFunc = field()
        type_: str | PickleStepType | None = field()
        parser: StepParser = field()
        anonymous_group_names: Iterable[str] | None = field()
        converters: Mapping[str, ConverterT] = field()
        params_fixtures_mapping: ParamsFixturesMapping = field()
        param_defaults: Mapping[str, object] = field()
        target_fixtures: Sequence[str] = field()
        liberal: bool | None = field()

        id: str = field(init=False)
        __cache: dict[int, StepDefinition] = field(factory=dict)

        @property
        def fixtures_mapped_from_step_definition(self) -> set[str]:
            """Handle fixtures mapped from step definition."""
            known_params = {
                *([] if self.anonymous_group_names is None else self.anonymous_group_names),
                *self.parser.arguments,
            }

            fixture_names = {*self.target_fixtures}
            converted_params: set[str]
            wildcard_params_strategy: object

            if isinstance(self.params_fixtures_mapping, Mapping):
                converted_params = {param for param in self.params_fixtures_mapping if isinstance(param, str)}
                fixture_names.update(
                    fixture_name
                    for fixture_name in self.params_fixtures_mapping.values()
                    if isinstance(fixture_name, str)
                )
                wildcard_params_strategy = getitemdefault(self.params_fixtures_mapping, ..., default=...)
            elif isinstance(self.params_fixtures_mapping, Collection):
                converted_params = set()
                wildcard_params_strategy = None
                fixture_names.update(self.params_fixtures_mapping)
            elif bool(self.params_fixtures_mapping):
                converted_params = set()
                wildcard_params_strategy = ...
            else:
                converted_params = set()
                wildcard_params_strategy = None

            if wildcard_params_strategy is ...:
                bypassed_params = known_params.difference(converted_params)
                fixture_names.update(bypassed_params)
            return fixture_names

        def as_message(self, config: Config | HasPytestStash) -> StepDefinition:
            """
            Convert to message representation.

            Returns:
                Step definition message.

            Raises:
                TypeError: If the operation cannot be completed.

            """
            id_generator = IdGenerator.from_stash(config.stash)
            try:
                message = self.__cache[id(id_generator)]
            except KeyError:
                self.id = id_generator.get_next_id()

                parser_expression_type = self.parser.type

                expression_type: StepDefinitionPatternType
                if isinstance(parser_expression_type, StepDefinitionPatternType):
                    expression_type = parser_expression_type
                else:
                    try:
                        expression_type = StepDefinitionPatternType(str(parser_expression_type))
                    except ValueError as exc:
                        msg = f"Unsupported step definition pattern type: {parser_expression_type!r}"
                        raise TypeError(msg) from exc

                pattern = StepDefinitionPattern(source=str(self.parser), pattern_type=expression_type)
                source_file, source_line = _resolve_callable_source_location(self.func)
                message = self.__cache[id(id_generator)] = StepDefinition(
                    id=self.id,
                    pattern=pattern,
                    source_reference=SourceReference(  # type: ignore[call-arg] # migration to pydantic2
                        uri=relpath(
                            source_file,
                            str(get_config_root_path(cast("Config", config))),
                        ),
                        location=Location(line=source_line, column=1),
                        java_method=JavaMethod(
                            class_name="pytest_bdd.steps.StepDefinition",
                            method_name=str(self.func.__name__),
                            method_parameter_types=[],
                        ),
                        java_stack_trace_element=JavaStackTraceElement(
                            class_name="pytest_bdd.steps.StepDefinition",
                            file_name=Path(source_file).name,
                            method_name=str(self.func.__name__),
                        ),
                    ),
                )
            return message

        def get_parameters(self, request: FixtureRequest, step: Step) -> dict[str, object]:
            """
            Get step parameters from parsed arguments.

            Returns:
                Dictionary of parameter names to values.

            """
            parsed_arguments = (
                self.parser.parse_arguments(request, step.text, anonymous_group_names=self.anonymous_group_names) or {}
            )
            return {
                **self.param_defaults,
                **{
                    arg: self.converters.get(arg, lambda value: value)(value) for arg, value in parsed_arguments.items()
                },
            }

    @runtime_checkable
    class StepProtocol(Protocol):
        """Protocol for callables carrying pytest-bdd step definitions."""

        __pytest_bdd_step_definitions__: set["StepDefinitionManager.Definition"]

    @runtime_checkable
    class NamespaceStepRegistryProtocol(Protocol):
        """Protocol for objects carrying a namespace step registry."""

        _step_registry: "StepDefinitionManager.Registry"

    @define
    class Registry:
        """Collection of step definitions with optional parent registry."""

        @runtime_checkable
        class RegistryFixtureProtocol(Protocol):
            """Protocol for fixtures carrying an attached step registry."""

            __pytest_bdd_step_registry__: "StepDefinitionManager.Registry"

        registry: set["StepDefinitionManager.Definition"] = field(factory=set)
        parent: "StepDefinitionManager.Registry | None" = field(default=None, init=False)

        @classmethod
        def inject_registry_fixture_and_register_steps(
            cls,
            namespace: "StepDefinitionManager.NamespaceStepRegistryProtocol",
        ) -> None:
            # Go around namespace and search for step definition containers
            """Handle inject registry fixture and register steps."""
            step_containers: list[StepDefinitionManager.StepProtocol] = [
                value for value in namespace.__dict__.values() if isinstance(value, StepDefinitionManager.StepProtocol)
            ]

            if not step_containers:
                return

            # Add step registry for a namespace if step containers were found
            step_definition_registry = cast(
                "StepDefinitionManager.Registry",
                setdefaultattr(
                    namespace,
                    "_step_registry",
                    value_factory=StepDefinitionManager.Registry,
                ),
            )
            setdefaultattr(namespace, "step_registry", step_definition_registry.fixture)
            step_definitions: list[StepDefinitionManager.Definition] = [
                step_definition
                for step_container in step_containers
                for step_definition in step_container.__pytest_bdd_step_definitions__
            ]
            step_definition_registry.registry.update(step_definitions)

            for fixture_name in (
                fixture_name
                for step_definition in step_definitions
                for fixture_name in step_definition.fixtures_mapped_from_step_definition
            ):

                def build_fixtures_mapped_from_step_definition(
                    fixture_name: str = fixture_name,
                ) -> Callable[[FixtureRequest], object | None]:
                    @pytest.fixture
                    def fixtures_mapped_from_step_definition(request: FixtureRequest) -> object | None:
                        """
                        Map step definition fixture.

                        Returns:
                            Fixture value or None if not found.

                        """
                        try:
                            return cast("object", request.getfixturevalue(fixture_name))
                        except FixtureLookupError:
                            return None

                    return fixtures_mapped_from_step_definition

                setdefaultattr(namespace, fixture_name, build_fixtures_mapped_from_step_definition())

        @property
        def fixture(self) -> Callable[["StepDefinitionManager.Registry"], "StepDefinitionManager.Registry"]:
            """Build the fixture that links a registry to its parent."""

            @pytest.fixture
            def step_registry(step_registry: "StepDefinitionManager.Registry") -> "StepDefinitionManager.Registry":
                self.parent = step_registry
                return self

            step_registry_typed = cast("StepDefinitionManager.Registry.RegistryFixtureProtocol", step_registry)
            step_registry_typed.__pytest_bdd_step_registry__ = self
            return step_registry

        def __iter__(self) -> Iterator["StepDefinitionManager.Definition"]:
            """
            Iterate over registered step definitions.

            Returns:
                Iterator over step definitions.

            """
            return iter(self.registry)

    @staticmethod
    def decorator_builder(  # noqa: PLR0913, PLR0917
        step_type: str | PickleStepType | None,
        step_parserlike: object,
        anonymous_group_names: Iterable[str] | None = None,
        converters: Mapping[str, ConverterT] | None = None,
        target_fixture: str | None = None,
        target_fixtures: Sequence[str] | None = None,
        params_fixtures_mapping: ParamsFixturesMapping = True,  # noqa:FBT002
        param_defaults: Mapping[str, object] | None = None,
        *,
        liberal: bool | None = None,
        stacklevel: int = 2,
    ) -> StepDecorator:
        """
        Step decorator for the type and the name.

        Args:
            step_type: Step type (CONTEXT, ACTION or OUTCOME).
            step_parserlike: Step name as in the feature file.
            anonymous_group_names: Grant names for anonymous groups of parserlike
            converters: Optional step arguments converters mapping
            target_fixture: Optional fixture name to replace by step definition
            target_fixtures: Target fixture names to be replaced by steps definition function.
            params_fixtures_mapping: Step parameters would be injected as fixtures
            param_defaults: Default parameters for step definition
            liberal: Could step definition be used with other keywords
            stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture

        Returns:
            Decorator function for the step.

        """
        converters = dict(converters or {})
        param_defaults = dict(param_defaults or {})
        if target_fixture is not None and target_fixtures is not None:
            warnings.warn(
                PytestBDDStepDefinitionWarning("Both target_fixture and target_fixtures are specified"),
                stacklevel=2,
            )
        resolved_target_fixtures: list[str] = list(
            OrderedSet(
                [
                    *([target_fixture] if target_fixture is not None else []),
                    *(target_fixtures if target_fixtures is not None else []),
                ],
            ),
        )

        def decorator(step_func: StepFunc) -> StepFunc:
            """
            Apply step decorator to function.

            Args:
                step_func: Step definition function

            Returns:
                Decorated step function.

            """
            step_definition = StepDefinitionManager.Definition(
                func=step_func,
                type_=step_type,
                parser=StepParser.build(step_parserlike),
                anonymous_group_names=anonymous_group_names,
                converters=converters,
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=param_defaults,
                target_fixtures=resolved_target_fixtures,
                liberal=liberal,
            )

            step_definitions = cast(
                "set[StepDefinitionManager.Definition]",
                setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set),
            )
            step_definitions.add(step_definition)

            # Allow step function to have same names, so injecting same steps with generated names into module scope
            converted_name = format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}")
            get_caller_module_locals(stacklevel=stacklevel)[converted_name] = step_func

            return step_func

        return decorator
