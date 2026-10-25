from __future__ import annotations

from functools import partial
from itertools import filterfalse
from operator import contains
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import TYPE_CHECKING, Any, cast

from pytest_cuke.model.message_extension import StepDefinitionPatternType
from pytest_cuke.parsers.base import StepParser, register_parser
from pytest_cuke.utils import stringify

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable

    from pytest_cuke.compatibility.pytest import FixtureRequest


class re(StepParser):
    type = StepDefinitionPatternType.pytest_cuke_regular_expression

    def __init__(self, pattern: object, *args: object, **kwargs: object) -> None:
        if isinstance(pattern, str):
            self.pattern = pattern
            compile_pattern = cast("Callable[..., _RePattern[Any]]", re_compile)
            self.regex = compile_pattern(pattern, *args, **kwargs)
        elif isinstance(pattern, _RePattern):
            if args or kwargs:
                raise TypeError("compiled regular expressions do not accept additional arguments")
            self.pattern = pattern.pattern
            self.regex = pattern
        else:
            raise NotImplementedError

    def parse_arguments(
        self,
        request: FixtureRequest,
        name: str,
        anonymous_group_names: Iterable[str] | None = None,
    ) -> dict[str, object]:
        regex = cast("_RePattern[str]", self.regex)
        match = cast("Match[str]", regex.fullmatch(name))
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
        regex = cast("_RePattern[str]", self.regex)
        return bool(regex.fullmatch(name))

    def __str__(self) -> str:
        return stringify(self.pattern)


register_parser(lambda parserlike: isinstance(parserlike, _RePattern), re)
