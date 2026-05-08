"""Provide parser helpers."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from attrs import define, field
from cucumber_messages import GherkinDocument  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator


@runtime_checkable
@define
class ParserProtocol(Protocol):
    """Define the parser protocol contract."""

    id_generator: IdGenerator | None = field(default=None, kw_only=True)

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> tuple[GherkinDocument, str]:  # pragma: no cover
        """Parse parse."""
        ...
