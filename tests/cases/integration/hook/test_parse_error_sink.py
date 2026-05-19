"""Provide test parse error sink helpers."""

from __future__ import annotations

from types import SimpleNamespace

from pytest_bdd.parser import BaseParser


def test_emit_parse_error_emits_through_hook_when_available() -> None:
    """Verify emit parse error emits through hook when available."""
    captured_messages = []

    def pytest_bdd_message(*, config, message) -> None:
        _ = config
        captured_messages.append(message)

    config = SimpleNamespace(hook=SimpleNamespace(pytest_bdd_message=pytest_bdd_message))

    BaseParser.emit_parse_error(
        config,
        message="parse failure",
        line=2,
        column=3,
        uri="file:features/example.feature",
    )

    assert len(captured_messages) == 1
    assert captured_messages[0].parse_error.message == "parse failure"
    assert captured_messages[0].parse_error.source.uri == "file:features/example.feature"


def test_emit_parse_error_uses_no_op_when_hook_is_missing() -> None:
    """Verify emit parse error uses no op when hook is missing."""
    config = SimpleNamespace()

    BaseParser.emit_parse_error(
        config,
        message="missing hook",
        line=1,
        column=1,
        uri="file:features/example.feature",
    )
