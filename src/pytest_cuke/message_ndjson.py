"""Read and validate canonical Cucumber Messages NDJSON streams."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pytest_cuke.model.message_stream_validation import MessageStreamValidator
from pytest_cuke.model.message_types import Envelope, message_from_dict
from pytest_cuke.model.message_validation import MessageValidationError, validate_envelope_data

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any


def iter_validated_ndjson(path: Path) -> Iterator[Envelope]:
    """Yield validated envelopes and report JSON, schema, and stream locations."""
    source = Path(path)
    if not source.is_file():
        raise ValueError(f"Messages NDJSON file does not exist: {source}")

    validator = MessageStreamValidator()
    record_lines: list[int] = []
    try:
        with source.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid Messages JSON in {source} at line {line_number}: {error.msg}") from error
                if not isinstance(payload, dict):
                    raise ValueError(
                        f"invalid Messages envelope in {source} at line {line_number}: expected a JSON object"
                    )

                raw_diagnostics = validate_envelope_data(
                    cast("dict[str, object]", payload),
                    position=len(record_lines),
                )
                if raw_diagnostics:
                    diagnostic = raw_diagnostics[0]
                    instance_location = (
                        " at /" + "/".join(str(part) for part in diagnostic.instance_path)
                        if diagnostic.instance_path
                        else ""
                    )
                    raise ValueError(
                        f"invalid Messages envelope in {source} at line {line_number} "
                        f"({diagnostic.code}){instance_location}: {diagnostic.message}"
                    )

                try:
                    envelope = message_from_dict(cast("dict[str, Any]", payload), Envelope)
                    accepted = validator.accept(envelope)
                except MessageValidationError as error:
                    diagnostic = error.diagnostics[0]
                    raise ValueError(
                        f"invalid Messages envelope in {source} at line {line_number} "
                        f"({diagnostic.code}): {diagnostic.message}"
                    ) from error
                except (TypeError, ValueError) as error:
                    raise ValueError(f"invalid Messages envelope in {source} at line {line_number}: {error}") from error

                record_lines.append(line_number)
                yield accepted
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read Messages NDJSON file {source}: {error}") from error

    diagnostics = validator.finish()
    if diagnostics:
        diagnostic = diagnostics[0]
        location = (
            f"line {record_lines[diagnostic.position]}"
            if diagnostic.position < len(record_lines)
            else f"end of file after line {record_lines[-1]}"
        )
        raise ValueError(
            f"invalid Messages stream in {source} at {location} "
            f"(record {diagnostic.position + 1}, {diagnostic.code}): {diagnostic.message}"
        )
    if not record_lines:
        raise ValueError(f"Messages NDJSON file contains no envelopes: {source}")


def read_validated_ndjson(path: Path) -> tuple[Envelope, ...]:
    """Parse and validate every NDJSON envelope and its stream before returning it."""
    return tuple(iter_validated_ndjson(path))


__all__ = ["iter_validated_ndjson", "read_validated_ndjson"]
