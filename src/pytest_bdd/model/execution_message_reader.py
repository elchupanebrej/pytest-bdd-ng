"""Read Cucumber Messages NDJSON into typed execution projections."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from pytest_bdd.model.execution_message_adapter import ExecutionProjection


def read_envelopes(messages_path: Path) -> Iterator[ExecutionProjection]:
    """Read NDJSON Cucumber Messages and yield typed execution projections."""
    with messages_path.open(encoding="utf-8") as f:
        for raw_line in f:
            stripped_line = raw_line.strip()
            if not stripped_line:
                continue
            try:
                envelope_dict = json.loads(stripped_line)
            except json.JSONDecodeError as exc:
                message = f"Malformed JSON on line: {stripped_line[:100]}"
                raise ValueError(message) from exc
            yield ExecutionMessageAdapter.deserialize_dict(envelope_dict)
