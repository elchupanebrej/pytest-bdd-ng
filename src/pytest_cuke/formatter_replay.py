"""Replay a saved Cucumber Messages stream through selected formatters."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.formatter_catalog import FormatterCatalogError
from pytest_cuke.formatter_runtime import FormatterRuntimeError, FormatterSession
from pytest_cuke.message_ndjson import iter_validated_ndjson
from pytest_cuke.model.message_types import (
    Envelope,
    TestRunFinished,
    Timestamp,
    message_from_dict,
    message_to_dict,
)
from pytest_cuke.model.report_presentation import ReportPresentation

if TYPE_CHECKING:
    from pytest_cuke.formatter_api import FormatterRequest

INCOMPLETE_MARKER_SUFFIX = ".incomplete.json"


def _mark_incomplete_reports(session: FormatterSession, source: Path, reason: str) -> tuple[Path, ...]:
    markers = []
    for output in session.published_outputs:
        marker = output.with_name(output.name + INCOMPLETE_MARKER_SUFFIX)
        marker.write_text(
            json.dumps(
                {
                    "incomplete": True,
                    "source": str(source),
                    "report": str(output),
                    "reason": reason,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        markers.append(marker)
    return tuple(markers)


def replay_messages(
    messages_path: Path,
    requests: tuple[FormatterRequest, ...],
    *,
    xfail_as_failed: bool = False,
    skip_as_failed: bool = False,
    tolerated_as_failed: bool = False,
    wip_as_failed: bool = False,
) -> None:
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
    presentation = ReportPresentation(
        xfail_as_failed=xfail_as_failed,
        skip_as_failed=skip_as_failed,
        tolerated_as_failed=tolerated_as_failed,
        wip_as_failed=wip_as_failed,
    )
    delivered = 0
    run_id: str | None = None
    incomplete: str | None = None
    finish_error: BaseException | None = None
    try:
        session.start()
        try:
            for message in iter_validated_ndjson(source):
                payload = message_to_dict(message)
                started = payload.get("testRunStarted")
                if isinstance(started, dict) and isinstance(started.get("id"), str):
                    run_id = started["id"]
                for envelope in presentation.accept(payload):
                    session.write_message(message_from_dict(envelope, Envelope))
                    delivered += 1
        except ValueError as error:
            if delivered == 0:
                raise FormatterRuntimeError(f"Messages stream cannot be replayed: {error}") from error
            incomplete = str(error)
        if incomplete is not None and run_id is not None:
            now = time.time()
            session.write_message(
                Envelope(
                    test_run_finished=TestRunFinished(
                        success=False,
                        timestamp=Timestamp(seconds=int(now), nanos=int(now % 1 * 1_000_000_000)),
                        message=f"incomplete Messages stream: {incomplete}",
                        test_run_started_id=run_id,
                    )
                )
            )
        try:
            session.finish(publish_incomplete=incomplete is not None)
        except BaseException as error:
            finish_error = error
    except BaseException:
        session.abort()
        raise

    if incomplete is not None:
        markers = _mark_incomplete_reports(session, source, incomplete)
        detail = f"Messages stream is incomplete: {incomplete}"
        if finish_error is not None and "incomplete Cucumber Messages stream" not in str(finish_error):
            detail += f"; formatter failure: {finish_error}"
        if markers:
            detail += f"; partial report(s) marked with {INCOMPLETE_MARKER_SUFFIX}"
        raise FormatterRuntimeError(detail)
    if finish_error is not None:
        raise finish_error


__all__ = ["replay_messages"]
