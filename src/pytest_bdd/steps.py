"""StepHandler decorators.

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
from collections.abc import Collection, Iterable, Iterator, Mapping, Sequence
from contextlib import suppress
from enum import Enum
from functools import partial
from inspect import getfile, getsourcelines
from typing import Any, Callable, Optional, Union, cast
from uuid import uuid4
from warnings import warn

import pytest
from _pytest.fixtures import FixtureRequest
from attr import Factory, attrib, attrs
from ordered_set import OrderedSet
from pydantic import ValidationError
from typing_extensions import Protocol, runtime_checkable

from messages import (  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]  # type:ignore[attr-defined, import-untyped]
    ExpressionType,
    Location,
    Pickle,
    SourceReference,
    StepDefinition,
    StepDefinitionPattern,
)
from messages import PickleStep as Step  # type:ignore[attr-defined]
from pytest_bdd.compatibility.path import relpath
from pytest_bdd.compatibility.pytest import Config, FixtureLookupError, Parser, get_config_root_path
from pytest_bdd.compatibility.typing import TypeAlias
from pytest_bdd.model import Feature, StepType
from pytest_bdd.model.messages_extension import ExpressionType as ExpressionTypeExtension
from pytest_bdd.parsers import StepParser
from pytest_bdd.types.protocol import PytestBDDIdGeneratorHandler
from pytest_bdd.types.warning import PytestBDDStepDefinitionWarning
from pytest_bdd.util.inspect_extra import get_caller_module_locals
from pytest_bdd.util.other import format_as_python_identifier
from pytest_bdd.util.toolz_extra import chain_map, flip, getitemdefault, setdefaultattr


class IniOptions(Enum):
    LIBERAL_STEPS = "liberal_steps"


class CliOptions(Enum):
    LIBERAL_STEPS = "liberal_steps"


def add_options(parser: Parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Steps")
    help_ = "Allow use different keywords with same step definition"
    group.addoption(
        "--liberal-steps",
        action="store_true",
        dest=CliOptions.LIBERAL_STEPS.value,
        default=None,
        help=help_,
    )
    parser.addini(
        IniOptions.LIBERAL_STEPS.value,
        default=False,
        type="bool",
        help=help_,
    )


def given(
    parserlike: Any,
    anonymous_group_names: Optional[Iterable[str]] = None,
    converters: Optional[dict[str, Callable]] = None,
    target_fixture: Optional[str] = None,
    target_fixtures: Optional[Sequence[str]] = None,
    params_fixtures_mapping: Union[set[str], dict[str, str], Any] = True,
    param_defaults: Optional[dict] = None,
    liberal: Optional[bool] = None,
    stacklevel=1,
) -> Callable:
    """Given step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.


    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.context,
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


def when(
    parserlike: Any,
    anonymous_group_names: Optional[Iterable[str]] = None,
    converters: Optional[dict[str, Callable]] = None,
    target_fixture: Optional[str] = None,
    target_fixtures: Optional[Sequence[str]] = None,
    params_fixtures_mapping: Union[set[str], dict[str, str], Any] = True,
    param_defaults: Optional[dict] = None,
    liberal: Optional[bool] = None,
    stacklevel=1,
) -> Callable:
    """When step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.action,
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


def then(
    parserlike: Any,
    anonymous_group_names: Optional[Iterable[str]] = None,
    converters: Optional[dict[str, Callable]] = None,
    target_fixture: Optional[str] = None,
    target_fixtures: Optional[Sequence[str]] = None,
    params_fixtures_mapping: Union[set[str], dict[str, str], Any] = True,
    param_defaults: Optional[dict] = None,
    liberal: Optional[bool] = None,
    stacklevel=1,
) -> Callable:
    """Then step decorator.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.outcome,
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


def step(
    parserlike: Any,
    anonymous_group_names: Optional[Iterable[str]] = None,
    converters: Optional[dict[str, Callable]] = None,
    target_fixture: Optional[str] = None,
    target_fixtures: Optional[Sequence[str]] = None,
    params_fixtures_mapping: Union[set[str], dict[str, str], Any] = True,
    param_defaults: Optional[dict] = None,
    liberal: Optional[bool] = None,
    stacklevel=1,
):
    """Liberal step decorator which could be used with any keyword.

    :param parserlike: StepHandler name or a parser object.
    :param anonymous_group_names: Grant names for anonymous groups of parserlike
    :param converters: Optional `dict` of the argument or parameter converters in form
                       {<param_name>: <converter function>}.
    :param target_fixture: Target fixture name to replace by steps definition function.
    :param target_fixtures: Target fixture names to be replaced by steps definition function.
    :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
    :param param_defaults: Default parameters for step definition
    :param liberal: Could step definition be used with other keywords
    :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture.

    :return: Decorator function for the step.
    """
    return StepHandler.decorator_builder(
        StepType.unknown,
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


class StepHandler:
    Model: TypeAlias = "Step"

    @attrs
    class Matcher:
        config: Config = attrib()
        feature: Feature = attrib(init=False)
        pickle: Pickle = attrib(init=False)
        step: Step = attrib(init=False)
        previous_step: Optional[Step] = attrib(init=False)
        step_registry: "StepHandler.Registry" = attrib(init=False)
        step_type_context = attrib(default=None)

        class MatchNotFoundError(RuntimeError):
            pass

        def __call__(
            self,
            request,
            feature: Feature,
            pickle: Pickle,
            step: Step,
            previous_step: Optional[Step],
            step_registry: "StepHandler.Registry",
        ) -> "StepHandler.Definition":
            self.request = request
            self.feature = feature
            self.pickle = pickle
            self.step = step
            self.previous_step = previous_step
            self.step_registry = step_registry

            self.step_type_context = (
                self.step_type_context
                if self.step.type is StepType.unknown and self.step_type_context is not None
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

        def strict_matcher(self, step_definition):
            return step_definition.type_ == self.step_type_context and step_definition.parser.is_matching(
                self.request,
                self.step.text,
            )

        def unspecified_matcher(self, step_definition):
            return (
                self.step_type_context == StepType.unknown or step_definition.type_ == StepType.unknown
            ) and step_definition.parser.is_matching(
                self.request,
                self.step.text,
            )

        def liberal_matcher(self, step_definition):
            if step_definition.liberal is None:
                if self.config.option.liberal_steps is not None:
                    is_step_definition_liberal = self.config.option.liberal_steps
                else:
                    is_step_definition_liberal = self.config.getini("liberal_steps")
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
            registry: Optional["StepHandler.Registry"],
            matchers: Sequence[Callable[["StepHandler.Definition"], bool]],
        ) -> Iterable["StepHandler.Definition"]:
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
                        yield from StepHandler.Matcher.find_step_definition_matches(registry.parent, matchers)

    @attrs(eq=False)
    class Definition:
        func: Callable = attrib()
        type_: Optional[Union[str, StepType]] = attrib()
        parser: StepParser = attrib()
        anonymous_group_names: Optional[Iterable[str]] = attrib()
        converters: dict[str, Callable] = attrib()
        params_fixtures_mapping: Union[  # type: ignore[valid-type]
            Collection[str],
            Mapping[Union[str, Any], Union[str, Any, None]],
            Any,
        ] = attrib()
        param_defaults: dict = attrib()
        target_fixtures: Sequence[str] = attrib()
        liberal: Optional[Any] = attrib()

        id = attrib(init=False)
        __cache: dict[int, StepDefinition] = attrib(default=Factory(dict))

        @property
        def fixtures_mapped_from_step_definition(self):
            known_params = {
                *([] if self.anonymous_group_names is None else self.anonymous_group_names),
                *([] if self.parser.arguments is None else self.parser.arguments),
            }

            fixture_names = {*self.target_fixtures}

            if isinstance(self.params_fixtures_mapping, Mapping):
                converted_params = {
                    *filter(
                        lambda param: param is not ...,
                        self.params_fixtures_mapping.keys(),
                    )
                }
                fixture_names.update(
                    filter(
                        lambda fixture_name: fixture_name is not None and fixture_name is not ...,
                        self.params_fixtures_mapping.values(),
                    ),
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

        def as_message(self, config: Union[Config, PytestBDDIdGeneratorHandler]):
            id_generator = cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator
            try:
                message = self.__cache[id(id_generator)]
            except KeyError:
                self.id = id_generator.get_next_id()

                parser_expression_type = self.parser.type

                expression_type: Union[ExpressionType, str]
                if isinstance(parser_expression_type, ExpressionType):
                    expression_type = parser_expression_type
                elif isinstance(parser_expression_type, ExpressionTypeExtension):
                    expression_type = parser_expression_type.value
                else:
                    expression_type = str(parser_expression_type)

                try:
                    pattern = StepDefinitionPattern(source=str(self.parser), type=expression_type)
                except ValidationError:
                    # Workaround because of https://github.com/cucumber/messages/issues/160
                    pattern = StepDefinitionPattern(source=str(self.parser), type=ExpressionType.regular_expression)
                message = self.__cache[id(id_generator)] = StepDefinition(
                    id=self.id,
                    pattern=pattern,
                    source_reference=SourceReference(  # type: ignore[call-arg] # migration to pydantic2
                        uri=relpath(
                            getfile(self.func),
                            str(get_config_root_path(cast(Config, config))),
                        ),
                        location=Location(line=getsourcelines(self.func)[1]),
                    ),
                )
            return message

        def get_parameters(self, request: FixtureRequest, step: Step):
            parsed_arguments = (
                self.parser.parse_arguments(request, step.text, anonymous_group_names=self.anonymous_group_names) or {}
            )
            return {
                **self.param_defaults,
                **{arg: self.converters.get(arg, lambda _: _)(value) for arg, value in parsed_arguments.items()},
            }

    @runtime_checkable
    class StepProtocol(Protocol):
        __pytest_bdd_step_definitions__: set["StepHandler.Definition"]

    @runtime_checkable
    class NamespaceStepRegistryProtocol(Protocol):
        _step_registry: "StepHandler.Registry"

    @attrs
    class Registry:
        registry: set["StepHandler.Definition"] = attrib(default=Factory(set))
        parent: "StepHandler.Registry" = attrib(default=None, init=False)

        @classmethod
        def inject_registry_fixture_and_register_steps(cls, namespace: "StepHandler.NamespaceStepRegistryProtocol"):
            # Go around namespace and search for step definition containers
            step_containers: list[StepHandler.StepProtocol] = list(
                filter(
                    partial(flip(isinstance), StepHandler.StepProtocol),
                    namespace.__dict__.values(),
                ),
            )

            if not step_containers:
                return

            # Add step registry for a namespace if step containers were found
            step_definition_registry: StepHandler.Registry = setdefaultattr(
                namespace,
                "_step_registry",
                value_factory=StepHandler.Registry,
            )
            setdefaultattr(namespace, "step_registry", step_definition_registry.fixture)
            step_definitions: list[StepHandler.Definition] = list(
                chain_map(
                    lambda step_container: step_container.__pytest_bdd_step_definitions__,
                    step_containers,
                ),
            )
            step_definition_registry.registry.update(step_definitions)

            for fixture_name in chain_map(
                lambda step_definition: step_definition.fixtures_mapped_from_step_definition,
                step_definitions,
            ):

                def build_fixtures_mapped_from_step_definition(fixture_name=fixture_name):
                    @pytest.fixture
                    def fixtures_mapped_from_step_definition(request):
                        try:
                            return request.getfixturevalue(fixture_name)
                        except FixtureLookupError:
                            ...

                    return fixtures_mapped_from_step_definition

                setdefaultattr(namespace, fixture_name, build_fixtures_mapped_from_step_definition())

        @property
        def fixture(self):
            @pytest.fixture
            def step_registry(step_registry):
                self.parent = step_registry
                return self

            step_registry.__pytest_bdd_step_registry__ = self
            return step_registry

        def __iter__(self) -> Iterator["StepHandler.Definition"]:
            return iter(self.registry)

    @staticmethod
    def decorator_builder(
        step_type: Optional[Union[str, StepType]],
        step_parserlike: Any,
        anonymous_group_names: Optional[Iterable[str]] = None,
        converters: Optional[dict[str, Callable]] = None,
        target_fixture: Optional[str] = None,
        target_fixtures: Optional[Sequence[str]] = None,
        params_fixtures_mapping: Union[set[str], dict[str, str], Any] = True,
        param_defaults: Optional[dict] = None,
        liberal: Optional[Any] = None,
        stacklevel=2,
    ) -> Callable:
        """StepHandler decorator for the type and the name.

        :param step_type: StepHandler type (CONTEXT, ACTION or OUTCOME).
        :param step_parserlike: StepHandler name as in the feature file.
        :param anonymous_group_names: Grant names for anonymous groups of parserlike
        :param converters: Optional step arguments converters mapping
        :param target_fixture: Optional fixture name to replace by step definition
        :param target_fixtures: Target fixture names to be replaced by steps definition function.
        :param params_fixtures_mapping: StepHandler parameters would be injected as fixtures
        :param param_defaults: Default parameters for step definition
        :param liberal: Could step definition be used with other keywords
        :param stacklevel: Stack level to find the caller frame. This is used when injecting the step definition fixture

        :return: Decorator function for the step.
        """
        converters = converters or {}
        param_defaults = param_defaults or {}
        if target_fixture is not None and target_fixtures is not None:
            warnings.warn(
                PytestBDDStepDefinitionWarning("Both target_fixture and target_fixtures are specified"), stacklevel=2
            )
        target_fixtures = list(
            OrderedSet(
                [
                    *([target_fixture] if target_fixture is not None else []),
                    *(target_fixtures if target_fixtures is not None else []),
                ],
            ),
        )

        def decorator(step_func: Callable) -> Callable:
            """StepHandler decorator

            :param function step_func: StepHandler definition function
            """
            step_definition = StepHandler.Definition(  # type: ignore[call-arg]
                func=step_func,
                type_=step_type,
                parser=StepParser.build(step_parserlike),
                anonymous_group_names=anonymous_group_names,
                converters=cast(dict, converters),
                params_fixtures_mapping=params_fixtures_mapping,
                param_defaults=cast(dict, param_defaults),
                target_fixtures=cast(list, target_fixtures),
                liberal=liberal,
            )

            setdefaultattr(step_func, "__pytest_bdd_step_definitions__", value_factory=set).add(step_definition)

            # Allow step function to have same names, so injecting same steps with generated names into module scope
            converted_name = format_as_python_identifier(f"step_{step_type or ''}_{step_parserlike}_{uuid4()}")
            get_caller_module_locals(stacklevel=stacklevel)[converted_name] = step_func

            return step_func

        return decorator
