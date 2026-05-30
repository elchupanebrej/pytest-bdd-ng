"""Step definition data class and shared type aliases."""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from inspect import getfile, getsourcelines
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias, cast

from _pytest.fixtures import FixtureRequest  # noqa: TC002
from attrs import define, field
from cucumber_messages import (  # type:ignore[attr-defined, import-untyped]
    JavaMethod,
    JavaStackTraceElement,
    Location,
    PickleStepType,
    SourceReference,
    StepDefinition,
    StepDefinitionPattern,
)
from cucumber_messages import PickleStep as Step  # type:ignore[attr-defined]
from typing_extensions import Protocol

from pytest_bdd.compatibility.path import resolvepath
from pytest_bdd.compatibility.pytest import Config  # noqa: TC001
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers import StepParser  # noqa: TC001
from pytest_bdd.types.protocol import HasPytestStash  # noqa: TC001
from pytest_bdd.util.other import IdGenerator
from pytest_bdd.util.toolz_extra import getitemdefault

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
                fixture_name for fixture_name in self.params_fixtures_mapping.values() if isinstance(fixture_name, str)
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

            pattern = StepDefinitionPattern(source=str(self.parser), type=expression_type)
            source_file, source_line = _resolve_callable_source_location(self.func)
            message = self.__cache[id(id_generator)] = StepDefinition(
                id=self.id,
                pattern=pattern,
                source_reference=SourceReference(  # type: ignore[call-arg] # migration to pydantic2
                    uri=Path(resolvepath(source_file, config.rootpath)).as_uri(),
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
            **{arg: self.converters.get(arg, lambda value: value)(value) for arg, value in parsed_arguments.items()},
        }
