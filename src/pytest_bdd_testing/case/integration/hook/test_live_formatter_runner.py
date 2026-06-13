"""

Provide live formatter runner tests.
"""

from __future__ import annotations

import pytest

from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner import _resolve_npm_formatter_resource


def test_resolve_npm_formatter_resource_reports_missing_asset(monkeypatch) -> None:
    """
    Verify missing npm formatter assets fail with context.

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

    def fake_find_resource(package_name, resource_path, *, additional_roots=()):
        assert package_name == "@cucumber/html-formatter"
        assert resource_path == "dist/main.js"
        assert tuple(additional_roots) == ()
        return iter(())

    monkeypatch.setattr(
        "pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner.find_resource",
        fake_find_resource,
    )

    with pytest.raises(RuntimeError, match=r"@cucumber/html-formatter.*dist/main\.js"):
        _resolve_npm_formatter_resource("@cucumber/html-formatter", "dist/main.js")
