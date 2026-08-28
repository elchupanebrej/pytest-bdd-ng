from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from attrs import define

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.utils import IdGenerator

if TYPE_CHECKING:
    try:
        from cucumber_messages import GherkinDocument
    except ImportError:
        from messages import GherkinDocument  # type: ignore[no-redef]


@define
class ParsedFeature:
    gherkin_document: GherkinDocument
    filename: str
    raw_data: str


@runtime_checkable
class ParserProtocol(Protocol):
    id_generator: IdGenerator | None = None

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> ParsedFeature: ...


__all__ = ["ParsedFeature", "ParserProtocol"]
