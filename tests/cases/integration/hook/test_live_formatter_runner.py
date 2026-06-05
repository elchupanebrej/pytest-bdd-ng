"""Provide live formatter runner tests."""

from __future__ import annotations

import pytest

from pytest_bdd.plugin.gherkin_message_reporter.live_formatter_runner import _resolve_npm_formatter_resource


def test_resolve_npm_formatter_resource_reports_missing_asset(monkeypatch) -> None:
    """Verify missing npm formatter assets fail with context."""

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
