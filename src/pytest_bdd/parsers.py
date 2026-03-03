from abc import ABC, abstractmethod
from collections.abc import Collection, Iterable, Sequence
from enum import Enum
from functools import partial, singledispatchmethod
from itertools import chain, filterfalse
from operator import attrgetter, contains, methodcaller
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Any, Protocol, Union, cast, runtime_checkable

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


class ParserBuildValueError(ValueError):
    def __init__(self, format_):
        super().__init__(f"Unable build parser for format {format_}")


@runtime_checkable
class StepParserProtocol(Protocol):
    type: StepDefinitionPatternType | str = StepDefinitionPatternType.pytest_bdd_other_expression  # type:ignore[attr-defined]

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, Any] | None: ...  # pragma: no cover

    @property
    def arguments(self) -> Collection[str]: ...  # pragma: no cover

    def is_matching(self, request: FixtureRequest, name: str) -> bool: ...  # pragma: no cover

    def __str__(self) -> str: ...  # pragma: no cover


class RegistryMode(Enum):
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
    ) -> dict[str, Any] | None:
        """Get step arguments from the given step name.

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
    def build(cls, parserlike: Union[str, bytes, "StepParser", StepParserProtocol]) -> "StepParser":
        """Get parser by given name.

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
    def __init__(self, *args, **kwargs):
        raise NotImplementedError  # pragma: no cover

    @__init__.register
    def _(self, pattern: str, *args: Any, **kwargs: Any) -> None:
        """Compile regex."""
        self.pattern = pattern
        self.regex = re_compile(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern):
        """Compile regex."""
        self.pattern = pattern.pattern
        self.regex = pattern

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name,
        anonymous_group_names: Iterable[str] | None = None,
    ):
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
    def arguments(self):
        return [*self.regex.groupindex.keys()]

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name,
    ):
        return bool(self.regex.fullmatch(name))

    def __str__(self):
        return normalize_to_string(self.pattern)


class parse(StepParser):  # noqa:N801 intentional API
    """parse step parser."""

    type = StepDefinitionPatternType.pytest_bdd_parse_expression  # type:ignore[attr-defined]

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, format_, *args, **kwargs):
        if isinstance(format_, (StringRepresentable, str, bytes)):
            self.__init_stringable__(format_, *args, **kwargs)
        else:
            raise ParserBuildValueError(format_)  # pragma: no cover

    def __init_stringable__(
        self,
        format_: StringRepresentable | str | bytes,
        *args: Any,
        builder=base_parse.compile,
        **kwargs: Any,
    ) -> None:
        self.format = normalize_to_string(format_)
        self.parser = builder(self.format, *args, **kwargs)

    @__init__.register
    def _(self, format_: base_parse.Parser):
        self.format = format_._format
        self.parser = format_

    @classmethod
    def cfparse(cls, *args, **kwargs):
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cls(*args, **kwargs)

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        match = self.parser.parse(name)
        group_dict = cast(dict, match.named)
        if anonymous_group_names is not None:
            group_dict.update(dict(zip(anonymous_group_names, match.fixed, strict=False)))
        return group_dict

    @property
    def arguments(self) -> Collection[str]:
        return [*self.parser._match_re.groupindex.keys()]

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name,
    ):
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self):
        return str(self.format)


class cfparse(parse):  # noqa:N801 intentional API
    """cfparse step parser."""

    type = StepDefinitionPatternType.pytest_bdd_cfparse_expression  # type:ignore[attr-defined]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


class string(StepParser):  # noqa: N801 intentional API
    """Exact string step parser."""

    type = StepDefinitionPatternType.pytest_bdd_string_expression  # type:ignore[attr-defined]

    def __init__(self, name: StringRepresentable | str | bytes) -> None:
        self.name = normalize_to_string(name)

    def parse_arguments(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,  # noqa: ARG002 overload
        anonymous_group_names: Iterable[str] | None = None,  # noqa: ARG002 overload
    ) -> dict[str, Any]:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    @property
    def arguments(self):
        return []

    def is_matching(
        self,
        request: FixtureRequest,  # noqa: ARG002 overload
        name: str,
    ) -> bool:
        """Match given name with the step name."""
        return bool(self.name == name)

    def __str__(self):
        return self.name


class _CucumberExpression(StepParser):
    pattern: str

    expression_type: type[CucumberExpression | CucumberRegularExpression]
    parameter_type_registry_like: ParameterTypeRegistry | Any
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
    ) -> dict[str, Any] | None:
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

    def __str__(self):
        return str(self.pattern)

    def rebuild_expression_in_test_context(self, request) -> CucumberExpression | CucumberRegularExpression:
        return self.expression_type(self.pattern, self._get_parameter_type_registry(request))

    def _get_parameter_type_registry(self, request) -> ParameterTypeRegistry | Any:
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
    type = StepDefinitionPatternType.cucumber_expression  # type:ignore[attr-defined]
    expression_type = CucumberExpression

    # https://bugs.python.org/issue45684
    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args, **kwargs):
        raise NotImplementedError  # pragma: no cover

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | Any = RegistryMode.FIXTURE,
    ):
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberExpression,
    ):
        self.pattern = expression.expression
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self):
        return []


class cucumber_regular_expression(_CucumberExpression):  # noqa: N801 intentional API
    type = StepDefinitionPatternType.regular_expression  # type:ignore[attr-defined]
    expression_type = CucumberRegularExpression
    # https://bugs.python.org/issue45684

    @singledispatchmethod  # type:ignore[misc]
    def __init__(self, *args, **kwargs):
        raise NotImplementedError  # pragma: no cover

    @__init__.register
    def _(
        self,
        expression: str,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | Any = RegistryMode.FIXTURE,
    ):
        self.pattern = expression
        self.parameter_type_registry_like = parameter_type_registry

    @__init__.register
    def _(
        self,
        expression: CucumberRegularExpression,
    ):
        self.pattern = expression.expression_regexp.pattern
        self.parameter_type_registry_like = expression.parameter_type_registry

    @property
    def arguments(self) -> Collection[str]:
        return [*re_compile(self.pattern).groupindex.keys()]


class heuristic(StepParser):  # noqa: N801 intentional API
    type = StepDefinitionPatternType.pytest_bdd_heuristic_expression  # type:ignore[attr-defined]

    def __init__(
        self,
        format_,
        parameter_type_registry: ParameterTypeRegistry | RegistryMode | Any | None = RegistryMode.FIXTURE,
    ):
        if isinstance(format_, (StringRepresentable, str, bytes)):
            self.format = normalize_to_string(format_)
        else:
            self.format = format_
        self.parameter_type_registry = parameter_type_registry
        self.parsers_are_built = False
        self.build_parsers()

    def build_parsers(self):
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
        return [
            self.string_parser,
            self.cucumber_expression_parser,
            self.cfparse_parser,
            self.re_parser,
        ]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        return any(
            map(
                methodcaller("is_matching", request, name),
                filter(bool, self.parser_by_priorities),
            )
        )

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, Any] | None:
        for parser in self.parser_by_priorities:
            if parser is not None and parser.is_matching(request, name):
                arguments = parser.parse_arguments(request, name, anonymous_group_names=anonymous_group_names)
                break
        else:
            arguments = None
        return arguments

    @property
    def arguments(self) -> Collection[str]:
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

    def __str__(self):
        return self.format
