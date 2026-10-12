from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from gherkin.ast_builder import AstBuilder
from gherkin.parser import Parser
from pytest import hookimpl

from pytest_cuke.compatibility.parser import ParsedFeature
from pytest_cuke.parser import ParserRegistration

if TYPE_CHECKING:
    from pytest_cuke.utils import IdGenerator

LEGACY_MIMETYPE = "application/x-legacy-gherkin"


class LegacyFeatureParser:
    """Small example extension using the historical config-aware parser shape."""

    id_generator: IdGenerator | None = None

    def parse(
        self,
        config: Any,
        path: Path,
        uri: str,
        *args: object,
        **kwargs: object,
    ) -> ParsedFeature:
        mode = os.environ.get("PYTEST_CUKE_LEGACY_MODE", "normal")
        if mode == "type-error":
            raise TypeError("intentional legacy parser failure")
        if mode == "malformed":
            return SimpleNamespace(gherkin_document=None, filename=str(path), raw_data="")  # type: ignore[return-value]

        encoding = str(kwargs.get("encoding", "utf-8"))
        source = path.read_text(encoding=encoding)
        if self.id_generator is None:
            raise RuntimeError("pytest-cuke did not provide the legacy parser's id_generator")
        id_sample = next(self.id_generator)
        config_sentinel = config.getoption("cuke_autoload")
        if config_sentinel is None:
            config_sentinel = config.getini("cuke_autoload")
        _write_invocation(
            {
                "path": str(path),
                "uri": uri,
                "config_sentinel": bool(config_sentinel),
                "encoding": encoding,
                "id_sample": id_sample,
            }
        )

        from pytest_cuke.model.message_types import GherkinDocument, message_from_dict  # noqa: PLC0415

        document_data = Parser(AstBuilder(id_generator=self.id_generator)).parse(source)
        document_data["uri"] = uri
        return ParsedFeature(
            gherkin_document=message_from_dict(document_data, GherkinDocument),
            filename=str(path.as_posix()),
            raw_data=source,
        )


def _write_invocation(invocation: dict[str, object]) -> None:
    log_path = Path(os.environ.get("PYTEST_CUKE_INVOCATION_LOG", "parser-invocations.json"))
    existing: list[dict[str, object]] = []
    if log_path.exists():
        existing = json.loads(log_path.read_text(encoding="utf-8"))
    existing.append(invocation)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


@hookimpl(tryfirst=True)
def pytest_cuke_get_mimetype(config: Any, path: Path) -> str | None:
    if path.name.casefold().endswith(".feature"):
        return LEGACY_MIMETYPE
    return None


@hookimpl(tryfirst=True)
def pytest_cuke_get_parser(config: Any, mimetype: str) -> ParserRegistration | None:
    if mimetype == LEGACY_MIMETYPE:
        return ParserRegistration.legacy(LegacyFeatureParser)
    return None
