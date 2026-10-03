from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.parser import GherkinParser, MarkdownParser
from pytest_cuke._native_go._types import NativeParserUnavailable

FEATURE_TEXT = "Feature: Backend selection\n  Scenario: Python remains available\n    Given a step\n"


def test_python_mode_never_initializes_native_library() -> None:
    with patch(
        "pytest_cuke._native_go._bridge._load_library",
        side_effect=AssertionError("Python mode initialized the native library"),
    ) as load_library:
        feature = GherkinParser().parse_text(FEATURE_TEXT, parser_mode="python")

    assert feature.name == "Backend selection"
    load_library.assert_not_called()


def test_auto_mode_falls_back_with_a_diagnostic_when_library_is_missing(caplog: pytest.LogCaptureFixture) -> None:
    with (
        patch("pytest_cuke._native_go._bridge._load_library", side_effect=OSError("library absent")),
        caplog.at_level(logging.WARNING, logger="pytest_cuke.parser_backend"),
    ):
        feature = GherkinParser().parse_text(FEATURE_TEXT, parser_mode="auto")

    assert feature.name == "Backend selection"
    assert "falling back to Python" in caplog.text
    assert "library absent" in caplog.text


def test_explicit_go_mode_fails_actionably_when_library_is_missing() -> None:
    with (
        patch("pytest_cuke._native_go._bridge._load_library", side_effect=OSError("library absent")),
        pytest.raises(NativeParserUnavailable, match=r"install Go.*build or reinstall"),
    ):
        GherkinParser().parse_text(FEATURE_TEXT, parser_mode="go")


def test_auto_mode_preserves_python_location_aware_syntax_error() -> None:
    native_error = '{"errorType":"syntax","errors":[{"message":"(3:1): bad step"}]}'
    content = "Feature: Broken\n  Scenario: Broken\n    Given a valid first step\n    Invalid syntax without keyword\n"

    with patch("pytest_cuke._native_go._bridge.parse_gherkin_document", return_value=native_error):
        with pytest.raises(FeatureConcreteParseError) as error:
            GherkinParser().parse_text(content, uri="broken.feature", parser_mode="auto")

    assert error.value.args[1] == 4
    assert error.value.args[3] == "broken.feature"


def test_auto_mode_uses_python_output_for_incompatible_markdown() -> None:
    native_empty_feature = '{"type":"GherkinDocument","feature":null,"comments":[]}'
    markdown = "# Feature: Markdown\n\n## Scenario: Python markdown\n* Given a step\n"

    with patch("pytest_cuke._native_go._bridge.parse_gherkin_markdown", return_value=native_empty_feature):
        feature = MarkdownParser().parse_text(markdown, parser_mode="auto")

    assert feature.name == "Markdown"
    assert feature.scenarios[0].name == "Python markdown"
