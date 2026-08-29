from __future__ import annotations

from collections.abc import Callable
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, TypeAlias, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import ParserBuildValueError, StepParser, register_parser
from pytest_bdd.utils import StringableProtocol, stringify

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest

_ParserBuilder: TypeAlias = Callable[..., base_parse.Parser]


class parse(StepParser):
    type = StepDefinitionPatternType.pytest_bdd_parse_expression

    @singledispatchmethod
    def __init__(self, format_: object, *args: object, **kwargs: object) -> None:
        if isinstance(format_, StringableProtocol | str | bytes):
            builder = cast("_ParserBuilder", kwargs.pop("builder", base_parse.compile))
            self._init_stringable(format_, *args, builder=builder, **kwargs)
        else:
            raise ParserBuildValueError(format_)

    def _init_stringable(
        self,
        format_: StringableProtocol | str | bytes,
        *args: object,
        builder: _ParserBuilder = base_parse.compile,
        **kw: object,
    ) -> None:
        self.format = stringify(format_)
        self.parser = cast("base_parse.Parser", builder(self.format, *args, **kw))

    @__init__.register
    def _(self, format_: base_parse.Parser) -> None:
        self.format, self.parser = format_._format, format_

    @classmethod
    def cfparse(cls, *args: object, **kwargs: object) -> parse:
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cast("parse", cls(*args, **kwargs))

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Iterable[str] | None = None
    ) -> dict[str, object]:
        match: Any = self.parser.parse(name)
        res = dict(match.named)
        if anonymous_group_names is not None:
            res.update(dict(zip(anonymous_group_names, match.fixed, strict=False)))
        return res

    @property
    def arguments(self) -> Collection[str]:
        return [*self.parser._match_re.groupindex.keys()]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self) -> str:
        return str(self.format)


class cfparse(parse):
    type = StepDefinitionPatternType.pytest_bdd_cfparse_expression

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


register_parser(lambda parserlike: isinstance(parserlike, base_parse.Parser), parse)
