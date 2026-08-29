from __future__ import annotations

from functools import partial, singledispatchmethod
from itertools import filterfalse
from operator import contains
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import TYPE_CHECKING, cast

from pytest_bdd.model.message_extension import StepDefinitionPatternType
from pytest_bdd.parsers.base import StepParser, register_parser
from pytest_bdd.utils import stringify

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest


class re(StepParser):
    type = StepDefinitionPatternType.pytest_bdd_regular_expression

    @singledispatchmethod
    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError

    @__init__.register
    def _(self, pattern: str, *args: object, **kwargs: object) -> None:
        self.pattern = pattern
        self.regex = re_compile(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern) -> None:  # type: ignore[type-arg]
        self.pattern = pattern.pattern
        self.regex = pattern

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        match = cast("Match[str]", self.regex.fullmatch(name))
        group_dict = match.groupdict()
        if anonymous_group_names is not None:
            named_spans = [*map(match.span, group_dict.keys())]
            anon_spans = filterfalse(partial(contains, named_spans), map(match.span, range(1, len(match.groups()) + 1)))
            group_dict.update(zip(anonymous_group_names, (name[slice(*span)] for span in anon_spans), strict=False))
        return {k: v for k, v in group_dict.items() if v is not None}

    @property
    def arguments(self) -> Collection[str]:
        return [*self.regex.groupindex.keys()]

    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        return bool(self.regex.fullmatch(name))

    def __str__(self) -> str:
        return stringify(self.pattern)


register_parser(lambda parserlike: isinstance(parserlike, _RePattern), re)
