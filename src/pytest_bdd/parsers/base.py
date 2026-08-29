from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Final, Protocol, TypeAlias, cast, runtime_checkable

from attrs import field, frozen

from pytest_bdd.model.message_extension import StepDefinitionPatternType

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable

    from pytest_bdd.compatibility.pytest import FixtureRequest

StepParserLike: TypeAlias = object


@frozen
class StepMatch:
    parameters: dict[str, Any] = field(factory=dict)
    parser: StepParserProtocol | None = None
    span: tuple[int, int] | None = None


class ParserBuildValueError(ValueError):
    def __init__(self, format_: object) -> None:
        super().__init__(f"Unable build parser for format {format_}")


class RegistryMode(Enum):
    NEW = "NEW"
    GLOBAL = "GLOBAL"
    FIXTURE = "FIXTURE"
    NOT_DEFINED = None


@runtime_checkable
class StepParserProtocol(Protocol):
    type: StepDefinitionPatternType | str = StepDefinitionPatternType.pytest_bdd_other_expression

    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Iterable[str] | None = None
    ) -> dict[str, Any] | None: ...
    @property
    def arguments(self) -> Collection[str]: ...
    def is_matching(self, request: FixtureRequest, name: str) -> bool: ...
    def __str__(self) -> str: ...


_PARSER_MODULES: Final = (
    "pytest_bdd.parsers.re_parser",
    "pytest_bdd.parsers.parse_parser",
    "pytest_bdd.parsers.cucumber_expression",
    "pytest_bdd.parsers.cucumber_regex",
    "pytest_bdd.parsers.heuristic",
)
_PARSER_REGISTRY: list[tuple[Callable[[StepParserLike], bool], Callable[[StepParserLike], object]]] = []
_FALLBACK_PARSER_BUILDER: Callable[[StepParserLike], object] | None = None
_PARSER_MODULES_LOADED = False


def register_parser(predicate: Callable[[StepParserLike], bool], builder: Callable[[StepParserLike], object]) -> None:
    _PARSER_REGISTRY.append((predicate, builder))


def register_fallback_parser(builder: Callable[[StepParserLike], object]) -> None:
    global _FALLBACK_PARSER_BUILDER  # noqa: PLW0603
    _FALLBACK_PARSER_BUILDER = builder


def _load_parser_modules() -> None:
    global _PARSER_MODULES_LOADED  # noqa: PLW0603
    if not _PARSER_MODULES_LOADED:
        for mod in _PARSER_MODULES:
            importlib.import_module(mod)
        _PARSER_MODULES_LOADED = True


class StepParser(StepParserProtocol, ABC):
    @abstractmethod
    def parse_arguments(
        self, request: FixtureRequest, name: str, anonymous_group_names: Iterable[str] | None = None
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    @property
    @abstractmethod
    def arguments(self) -> Collection[str]:
        raise NotImplementedError

    @abstractmethod
    def is_matching(self, request: FixtureRequest, name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    @classmethod
    def build(cls, parserlike: StepParserLike) -> StepParser:
        if isinstance(parserlike, StepParserProtocol):
            return cast("StepParser", parserlike)
        _load_parser_modules()
        for predicate, builder in _PARSER_REGISTRY:
            if predicate(parserlike):
                return cast("StepParser", builder(parserlike))
        if _FALLBACK_PARSER_BUILDER is None:
            raise ParserBuildValueError(parserlike)
        return cast("StepParser", _FALLBACK_PARSER_BUILDER(parserlike))
