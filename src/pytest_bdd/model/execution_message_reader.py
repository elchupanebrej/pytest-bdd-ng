"""
Read Cucumber Messages NDJSON into typed execution projections.

Responsibility:
    Provides file-level reading for Cucumber Messages NDJSON streams and converts each envelope
    into an ExecutionProjection. Owns the narrow boundary between raw message files and typed
    execution data consumed by reporting code.

Reason for existence:
    Keeps low-level NDJSON parsing separate from execution adapters so callers can consume typed
    projections without knowing message serialization details.

Delegates:
    - json: Parses each non-empty NDJSON line.
    - ExecutionMessageAdapter: Converts envelope dictionaries into execution projections.

Cohesion:
    All module behavior serves one data-loading path: NDJSON line input to typed projection output.

Separation:
    Parser error handling stays here; model adaptation stays in execution_message_adapter.

Main consumers:
    - pytest_bdd reporting and verification code that needs typed execution projections from files.

State and side effects:
    Opens the provided message file for reading. Does not mutate global state.

Invariants:
    - Empty lines are ignored.
    - Malformed JSON raises ValueError with a short offending-line preview.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=3
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pytest_bdd.model.execution_message_adapter import ExecutionMessageAdapter

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from pytest_bdd.model.execution_message_adapter import ExecutionProjection


def read_envelopes(messages_path: Path) -> Iterator[ExecutionProjection]:
    """
    Read NDJSON Cucumber Messages and yield typed execution projections.

    Responsibility:
        Iterates over a Cucumber Messages NDJSON file and yields one typed ExecutionProjection per
        non-empty line. Owns line filtering, JSON parse errors, and streaming conversion for one
        message file.

    Reason for existence:
        Gives callers a streaming reader that reports malformed JSON with a useful local error while
        keeping conversion delegated to ExecutionMessageAdapter.

    Delegates:
        - Path.open: Opens the message stream.
        - json.loads: Parses envelope JSON.
        - ExecutionMessageAdapter.deserialize_dict: Builds typed projections.

    Cohesion:
        The function performs one complete read/parse/adapt loop for NDJSON envelopes.

    Separation:
        It does not interpret execution semantics; adapter logic owns that translation.

    Main consumers:
        - Tests and reporting utilities that need typed execution data from message files.

    State and side effects:
        Reads from messages_path. No writes, subprocesses, or global state mutation.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=4
    """
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
