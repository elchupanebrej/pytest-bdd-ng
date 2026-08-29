from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, cast, runtime_checkable

from attrs import field, frozen

from pytest_bdd.model.message_extension import StepDefinitionPatternType

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

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
        raise ParserBuildValueError(parserlike)
