from pathlib import Path
from typing import Protocol, runtime_checkable

from attr import attrib, attrs
from cucumber_messages import GherkinDocument  # type:ignore[attr-defined, import-untyped]

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.types.protocol import HasPytestStash
from pytest_bdd.util.other import IdGenerator


@runtime_checkable
@attrs
class ParserProtocol(Protocol):
    id_generator: IdGenerator | None = attrib(default=None, kw_only=True)

    def parse(
        self,
        config: Config | HasPytestStash,
        path: Path,
        uri: str,
        *args,
        **kwargs,
    ) -> tuple[GherkinDocument, str]:  # pragma: no cover
        ...
