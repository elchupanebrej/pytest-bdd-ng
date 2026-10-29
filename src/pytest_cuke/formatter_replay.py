"""Replay a saved Cucumber Messages stream through selected formatters."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.formatter_catalog import FormatterCatalogError
from pytest_cuke.formatter_runtime import FormatterSession
from pytest_cuke.message_ndjson import iter_validated_ndjson

if TYPE_CHECKING:
    from pytest_cuke.formatter_api import FormatterRequest


def replay_messages(messages_path: Path, requests: tuple[FormatterRequest, ...]) -> None:
    """Validate and render a saved stream using the same runtime as live formatters."""
    source = Path(messages_path).resolve(strict=False)
    if not source.is_file():
        raise ValueError(f"Messages NDJSON file does not exist: {source}")

    for request in requests:
        output_path = request.output_path
        if output_path is not None and output_path.resolve(strict=False) == source:
            raise FormatterCatalogError(
                f"Replay formatter {request.name!r} output path is the Messages input file: {source}"
            )

    session = FormatterSession(None, requests, mode="replay")
    try:
        session.start()
        for message in iter_validated_ndjson(source):
            session.write_message(message)
        session.finish()
    except BaseException:
        session.abort()
        raise


__all__ = ["replay_messages"]
