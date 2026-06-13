"""

Provide test parse error sink helpers.
"""

from __future__ import annotations

from types import SimpleNamespace

from pytest_bdd.parser import BaseParser


def test_emit_parse_error_emits_through_hook_when_available() -> None:
    """
    Verify emit parse error emits through hook when available.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
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
    """
    Verify emit parse error uses no op when hook is missing.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    config = SimpleNamespace()

    BaseParser.emit_parse_error(
        config,
        message="missing hook",
        line=1,
        column=1,
        uri="file:features/example.feature",
    )
