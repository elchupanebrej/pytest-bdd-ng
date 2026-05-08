"""Provide parsers helpers."""

from abc import ABC, abstractmethod
from collections.abc import Collection, Iterable, Sequence
from enum import Enum
from functools import partial, singledispatchmethod
from itertools import chain, filterfalse
from operator import attrgetter, contains, methodcaller
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Protocol, TypeAlias, cast, runtime_checkable

import parse as base_parse
import parse_type.cfparse as base_cfparse
from cucumber_expressions.errors import CantEscape, UndefinedParameterTypeError
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

from pytest_bdd.compatibility.pytest import FixtureRequest
from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.util.other import StringRepresentable, normalize_to_string

UNDEFINED_PARAMETER_TYPE_PATTERN = re_compile(
    r"Undefined parameter type ['{]?(?P<name>[^'}.\n]+)['}]?\.?",
)

StepParserLike: TypeAlias = object


class _ParseMatchProtocol(Protocol):
    named: dict[str, object]
    fixed: Sequence[object]


class _ParserBuilder(Protocol):
    def __call__(self, format_: str, *args: object, **kwargs: object) -> object: ...


class _RegexCompiler(Protocol):
    def __call__(self, pattern: str, *args: object, **kwargs: object) -> _RePattern[str]: ...


class ParserBuildValueError(ValueError):
    """Represent parser build value error failures."""

    def __init__(self, format_: object) -> None:
        """Initialize the parser build value error."""
        super().__init__(f"Unable build parser for format {format_}")


@runtime_checkable
class StepParserProtocol(Protocol):
    """Define the step parser protocol contract."""

    type: StepDefinitionPatternType | str = StepDefinitionPatternType.pytest_bdd_other_expression  # type:ignore[attr-defined]

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """Parse arguments."""
        ...  # pragma: no cover

    @property
    def arguments(self) -> Collection[str]:
        """Handle arguments."""
        ...  # pragma: no cover

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """Return matching."""
        ...  # pragma: no cover

    def __str__(self) -> str:
        """Return parser pattern as a string."""
        ...  # pragma: no cover


class RegistryMode(Enum):
    """Represent registry mode state."""

    NEW = "NEW"
    GLOBAL = "GLOBAL"
    FIXTURE = "FIXTURE"
    NOT_DEFINED = None


class StepParser(StepParserProtocol, ABC):
    """Parser of the individual step."""

    @abstractmethod
    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """
        Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        raise NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def arguments(self) -> Collection[str]:
        """Get step argument names from the given step name."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """Match given name with the step name."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def __str__(self) -> str:
        """Match given name with the step name."""
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def build(cls, parserlike: StepParserLike) -> "StepParser":
        """
        Get parser by given name.

        :param parserlike: name of the step to parse

        :return: step parser object
        :rtype: StepParser
        """
        if isinstance(parserlike, StepParserProtocol):
            parser = cast(StepParser, parserlike)
        elif isinstance(parserlike, _RePattern):
            parser = re(parserlike)
        elif isinstance(parserlike, base_parse.Parser):
            parser = parse(parserlike)
        elif isinstance(parserlike, CucumberExpression):
            parser = cucumber_expression(parserlike)
        elif isinstance(parserlike, CucumberRegularExpression):
            parser = cucumber_regular_expression(parserlike)
        else:
            parser = heuristic(parserlike)

        return parser


class re(StepParser):  # noqa:N801 intentional API
    """Regex step parser."""

    type = StepDefinitionPatternType.pytest_bdd_regular_expression  # type:ignore[attr-defined]

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the re.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        """
        raise NotImplementedError  # pragma: no cover

    @__init__.register
    def _(self, pattern: str, *args: object, **kwargs: object) -> None:
        """Compile regex."""
        self.pattern = pattern
        self.regex = cast(_RegexCompiler, re_compile)(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern[str]) -> None:
        """Compile regex."""
        self.pattern = pattern.pattern
        self.regex = pattern

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        """Parse arguments."""
        match = cast(Match, self.regex.fullmatch(name))  # Can't be None because is already matched
        group_dict = match.groupdict()
        if anonymous_group_names is not None:
            group_dict.update(
                zip(
                    anonymous_group_names,
                    (
                        name[slice(*span)]
                        for span in filterfalse(
                            partial(contains, [*map(match.span, group_dict.keys())]),
                            map(match.span, range(1, len(match.groups()) + 1)),
                        )
                    ),
                    strict=False,
                ),
            )

        return {k: v for k, v in group_dict.items() if v is not None}

    @property
    def arguments(self) -> Collection[str]:
        """Handle arguments."""
        return [*self.regex.groupindex.keys()]

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """Return matching."""
        return bool(self.regex.fullmatch(name))

    def __str__(self) -> str:
        """Return parser pattern as a string."""
        return normalize_to_string(self.pattern)


class parse(StepParser):  # noqa:N801 intentional API
    """
    Initialize the instance.

    Raises:
        ParserBuildValueError: If the operation cannot be completed.

    """

    """parse step parser."""

    type = StepDefinitionPatternType.pytest_bdd_parse_expression  # type:ignore[attr-defined]

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, format_: object, *args: object, **kwargs: object) -> None:
        """
        Initialize the parse.

        Raises:
            ParserBuildValueError: If the operation cannot be completed.

        """
        if isinstance(format_, (StringRepresentable, str, bytes)):
            builder = cast(_ParserBuilder, kwargs.pop("builder", base_parse.compile))
            self._init_stringable(format_, *args, builder=builder, **kwargs)
        else:
            raise ParserBuildValueError(format_)  # pragma: no cover

    def _init_stringable(
        self,
        format_: StringRepresentable | str | bytes,
        *args: object,
        builder: _ParserBuilder = base_parse.compile,
        **kwargs: object,
    ) -> None:
        self.format = normalize_to_string(format_)
        self.parser = cast(base_parse.Parser, builder(self.format, *args, **kwargs))

    @__init__.register
    def _(self, format_: base_parse.Parser) -> None:
        self.format = format_._format
        self.parser = format_

    @classmethod
    def cfparse(cls, *args: object, **kwargs: object) -> "parse":
        """Handle cfparse."""
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cast(parse, cls(*args, **kwargs))

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        """Parse arguments."""
        match = cast(_ParseMatchProtocol, self.parser.parse(name))
        group_dict = dict(match.named)
        if anonymous_group_names is not None:
            group_dict.update(dict(zip(anonymous_group_names, match.fixed, strict=False)))
        return group_dict

    @property
    def arguments(self) -> Collection[str]:
        """Handle arguments."""
        return [*self.parser._match_re.groupindex.keys()]

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """Return matching."""
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self) -> str:
        """Return parser format as a string."""
        return str(self.format)


class cfparse(parse):  # noqa:N801 intentional API
    """Initialize the instance."""

    """cfparse step parser."""

    type = StepDefinitionPatternType.pytest_bdd_cfparse_expression  # type:ignore[attr-defined]

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize the cfparse."""
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


class string(StepParser):  # noqa: N801 intentional API
    """Exact string step parser."""

    type = StepDefinitionPatternType.pytest_bdd_string_expression  # type:ignore[attr-defined]

    def __init__(self, name: StringRepresentable | str | bytes) -> None:
        """Initialize the string."""
        self.name = normalize_to_string(name)

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,  # noqa: ARG002 overload
        anonymous_group_names: Iterable[str] | None = None,  # noqa: ARG002 overload
    ) -> dict[str, object]:
        """
        No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    @property
    def arguments(self) -> Collection[str]:
        """Handle arguments."""
        return []

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """Match given name with the step name."""
        return bool(self.name == name)

    def __str__(self) -> str:
        """Return the exact step name."""
        return self.name


class _CucumberExpression(StepParser):
    pattern: str

    expression_type: type[CucumberExpression] | type[CucumberRegularExpression]
    parameter_type_registry_like: ParameterTypeRegistry | RegistryMode | str | None
    parameter_type_registry = ParameterTypeRegistry()  # default registry
    last_undefined_parameter_type: tuple[str, str] | None = None

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        try:
            self.last_undefined_parameter_type = None
            return bool(self.rebuild_expression_in_test_context(request).tree_regexp.match(name))
        except UndefinedParameterTypeError as exc:
            expression = self.pattern
            undefined_name = ""
            for arg in exc.args:
                matched_name = UNDEFINED_PARAMETER_TYPE_PATTERN.search(str(arg))
                if matched_name:
                    undefined_name = matched_name.group("name")
                    break
            self.last_undefined_parameter_type = (expression, undefined_name)
            return False
        except CantEscape:
            self.last_undefined_parameter_type = None
            return False

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        return dict(
            zip(
                anonymous_group_names or [],
                map(
                    attrgetter("value"),
                    self.rebuild_expression_in_test_context(request).match(name) or [],
                ),
                strict=False,
            ),
        )

    def __str__(self) -> str:
        return str(self.pattern)

    def rebuild_expression_in_test_context(
        self,
        request: FixtureRequest,
    ) -> CucumberExpression | CucumberRegularExpression:
        return self.expression_type(self.pattern, self._get_parameter_type_registry(request))

    def _get_parameter_type_registry(self, request: FixtureRequest) -> ParameterTypeRegistry:
        if (
            isinstance(self.parameter_type_registry_like, (str, RegistryMode))
            or self.parameter_type_registry_like is None
        ):
            parameter_type_registry_mode = RegistryMode(self.parameter_type_registry_like)

            parameter_type_registry = {
                RegistryMode.NEW: ParameterTypeRegistry,
                RegistryMode.GLOBAL: lambda: self.parameter_type_registry,
                RegistryMode.NOT_DEFINED: lambda: self.parameter_type_registry,
                RegistryMode.FIXTURE: lambda: request.getfixturevalue("parameter_type_registry"),
            }[parameter_type_registry_mode]()
        else:
            parameter_type_registry = self.parameter_type_registry_like
        return parameter_type_registry


class cucumber_expression(_CucumberExpression):  # noqa: N801 intentional API
    """
    Represent cucumber expression state.

    Raises:
        NotImplementedError: If the operation cannot be completed.

    """

    type = StepDefinitionPatternType.cucumber_expression  # type:ignore[attr-defined]
    expression_type = CucumberExpression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the cucumber expression.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        """
        raise NotImplementedError  # pragma: no cover

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberExpression,
    ) -> None:
        """Handle object."""
        self.pattern = expression.expression
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        """Handle arguments."""
        return []


class cucumber_regular_expression(_CucumberExpression):  # noqa: N801 intentional API
    """
    Represent cucumber regular expression state.

    Raises:
        NotImplementedError: If the operation cannot be completed.

    """

    type = StepDefinitionPatternType.regular_expression  # type:ignore[attr-defined]
    expression_type = CucumberRegularExpression
    # https://bugs.python.org/issue45684

    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args: object, **kwargs: object) -> None:
        """
        Initialize the cucumber regular expression.

        Raises:
            NotImplementedError: If the operation cannot be completed.

        """
        raise NotImplementedError  # pragma: no cover

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberRegularExpression,
    ) -> None:
        self.pattern = expression.expression_regexp.pattern
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        """Initialize the cucumber regular expression."""
        """Initialize the cucumber regular expression."""
        return [*re_compile(self.pattern).groupindex.keys()]


class heuristic(StepParser):  # noqa: N801 intentional API
    """
    Represent heuristic state.

    Raises:
        ParserBuildValueError: If the operation cannot be completed.

    """

    type = StepDefinitionPatternType.pytest_bdd_heuristic_expression  # type:ignore[attr-defined]

    def __init__(
        self,
        format_: object,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | str | None = RegistryMode.FIXTURE,
    ) -> None:
        """Initialize the heuristic."""
        if isinstance(format_, (StringRepresentable, str, bytes)):
            self.format = normalize_to_string(format_)
        else:
            self.format = format_
        self.parameter_type_registry = parameter_type_registry
        self.parsers_are_built = False
        self.build_parsers()

    def build_parsers(self) -> None:
        """
        Build parsers.

        Raises:
            ParserBuildValueError: If the operation cannot be completed.

        """
        if self.parsers_are_built:
            return

        # Rework to exception groups after python 3.10 end of support
        e_cause = None
        try:
            self.string_parser: string | None = string(self.format)
        except Exception as e:  # noqa: BLE001 intentional
            e_cause = e
            self.string_parser = None
        try:
            self.cucumber_expression_parser = cucumber_expression(
                self.format,
                parameter_type_registry=self.parameter_type_registry,
            )
        except Exception as e:  # noqa: BLE001 intentional
            e.__cause__, e_cause = e_cause, e
            self.cucumber_expression_parser = None

        try:
            self.cfparse_parser: cfparse | None = cfparse(self.format)
        except Exception as e:  # noqa: BLE001 intentional
            e.__cause__, e_cause = e_cause, e
            self.cfparse_parser = None

        try:
            self.re_parser = re(self.format)
        except Exception as e:  # noqa: BLE001 intentional
            e.__cause__, e_cause = e_cause, e
            self.re_parser = None

        self.parsers_are_built = True
        if not any(self.parser_by_priorities):
            raise ParserBuildValueError(self.format) from e_cause  # pragma: no cover

    @property
    def parser_by_priorities(self) -> Sequence[StepParser | None]:
        """Handle parser by priorities."""
        """Handle parser by priorities."""
        return [
            self.string_parser,
            self.cucumber_expression_parser,
            self.cfparse_parser,
            self.re_parser,
        ]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        """Return matching."""
        return any(
            map(
                methodcaller("is_matching", request, name),
                filter(bool, self.parser_by_priorities),
            ),
        )

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object] | None:
        """Parse arguments."""
        for parser in self.parser_by_priorities:
            if parser is not None and parser.is_matching(request, name):
                arguments = parser.parse_arguments(request, name, anonymous_group_names=anonymous_group_names)
                break
        else:
            arguments = None
        return arguments

    @property
    def arguments(self) -> Collection[str]:
        """Handle arguments."""
        return [
            *chain.from_iterable(
                (
                    (
                        []  # type:ignore[no-any-return]
                        if (args := getattr(parser, "arguments", None)) is None
                        else args
                    )
                    for parser in self.parser_by_priorities
                ),
            ),
        ]

    def __str__(self) -> str:
        """Return parser format as a string."""
        return str(self.format)
