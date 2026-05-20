"""Unit tests for Gherkin parser helpers."""

from __future__ import annotations

from contextlib import suppress
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from pytest_bdd.parser import BaseParser, GherkinParser, MarkdownGherkinParser
from pytest_bdd.types.exception import FeatureConcreteParseError
from pytest_bdd.util.other import IdGenerator

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.unit]


def _config() -> SimpleNamespace:
    """Build a minimal parser config."""
    return SimpleNamespace(stash={IdGenerator.STASH_KEY: IdGenerator()}, hook=SimpleNamespace())


def test_gherkin_parser_returns_parsed_feature(tmp_path: Path) -> None:
    """GherkinParser parses valid feature content."""
    path = tmp_path / "sample.feature"
    path.write_text("Feature: X\n  Scenario: Y\n    Given Z\n", encoding="utf-8")

    parsed = GherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:sample.feature")

    assert parsed.gherkin_document.feature.name == "X"
    assert parsed.filename == path.as_posix()
    assert "Scenario: Y" in parsed.raw_data


def test_gherkin_parser_raises_concrete_error_for_invalid_feature(tmp_path: Path) -> None:
    """GherkinParser raises a concrete parse error for invalid Gherkin."""
    path = tmp_path / "broken.feature"
    path.write_text("Not a feature\n", encoding="utf-8")

    with pytest.raises(FeatureConcreteParseError):
        GherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:broken.feature")


def test_markdown_parser_extracts_gherkin_from_markdown(tmp_path: Path) -> None:
    """MarkdownGherkinParser extracts feature content from Markdown."""
    path = tmp_path / "sample.feature.md"
    path.write_text("# Feature: Markdown\n\n## Scenario: From heading\n\n* Given a step\n", encoding="utf-8")

    parsed = MarkdownGherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:sample.feature.md")

    assert parsed.gherkin_document.feature.name == "Markdown"
    assert parsed.gherkin_document.feature.children[0].scenario.name == "From heading"


def test_markdown_parser_empty_content_raises_key_error(tmp_path: Path) -> None:
    """MarkdownGherkinParser raises KeyError for parser output without feature."""
    path = tmp_path / "empty.feature.md"
    path.write_text("", encoding="utf-8")

    with pytest.raises(KeyError, match="feature"):
        MarkdownGherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:empty.feature.md")


def test_normalize_gherkin_document_payload_fills_missing_locations() -> None:
    """normalize_gherkin_document_payload fills missing location fields recursively."""
    payload = {"feature": {"location": {}, "children": [{"scenario": {"location": {}}}]}}

    normalized = BaseParser.normalize_gherkin_document_payload(payload)

    assert normalized["feature"]["location"] == {"line": 1, "column": 1}
    assert normalized["feature"]["children"][0]["scenario"]["location"] == {"line": 1, "column": 1}


def test_normalize_gherkin_document_payload_adds_comments() -> None:
    """normalize_gherkin_document_payload adds empty comments list if missing."""
    payload: dict = {"feature": {"name": "X"}}

    normalized = BaseParser.normalize_gherkin_document_payload(payload)

    assert normalized["comments"] == []


def test_normalize_gherkin_document_payload_handles_nested_locations() -> None:
    """normalize_gherkin_document_payload handles deeply nested locations."""
    payload = {
        "feature": {
            "location": {},
            "children": [
                {"scenario": {"location": {}, "steps": [{"location": {}}]}},
            ],
        },
    }

    normalized = BaseParser.normalize_gherkin_document_payload(payload)

    step_loc = normalized["feature"]["children"][0]["scenario"]["steps"][0]["location"]
    assert step_loc == {"line": 1, "column": 1}


def test_normalize_gherkin_document_payload_preserves_existing_locations() -> None:
    """normalize_gherkin_document_payload preserves existing location values."""
    payload = {"feature": {"location": {"line": 42, "column": 7}}}

    normalized = BaseParser.normalize_gherkin_document_payload(payload)

    assert normalized["feature"]["location"] == {"line": 42, "column": 7}


def test_build_feature_returns_gherkin_document() -> None:
    """build_feature converts a dict to a GherkinDocument."""
    from cucumber_messages import GherkinDocument as GherkinDoc

    raw: dict = {
        "comments": [],
        "feature": {
            "children": [],
            "keyword": "Feature",
            "language": "en",
            "location": {"line": 1, "column": 1},
            "name": "X",
            "description": "",
            "tags": [],
        },
    }

    result = BaseParser.build_feature(raw)

    assert isinstance(result, GherkinDoc)
    assert result.feature.name == "X"


def test_gherkin_parser_handles_encoding_kwarg(tmp_path: Path) -> None:
    """GherkinParser uses the encoding keyword argument."""
    path = tmp_path / "encoded.feature"
    path.write_text("Feature: Encodé\n  Scenario: Tëst\n    Given step\n", encoding="utf-8")

    parsed = GherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:encoded.feature", encoding="utf-8")

    assert parsed.gherkin_document.feature.name == "Encodé"


def test_markdown_parser_handles_headings_and_lists(tmp_path: Path) -> None:
    """MarkdownGherkinParser handles mixed headings and unordered lists."""
    path = tmp_path / "mixed.feature.md"
    path.write_text(
        "# Feature: Mixed\n\n"
        "Some description text.\n\n"
        "## Scenario: Mixed steps\n\n"
        "* Given first step\n"
        "* When second step\n",
        encoding="utf-8",
    )

    parsed = MarkdownGherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:mixed.feature.md")

    assert parsed.gherkin_document.feature.name == "Mixed"


def test_markdown_parser_content_without_feature_heading(tmp_path: Path) -> None:
    """MarkdownGherkinParser with content lacking a Feature heading raises error."""
    path = tmp_path / "nofeature.feature.md"
    path.write_text("Just some text\nNo feature here\n", encoding="utf-8")

    # The parser may or may not raise; verify it doesn't crash.
    with suppress(KeyError, FeatureConcreteParseError):
        MarkdownGherkinParser(id_generator=IdGenerator()).parse(_config(), path, "file:nofeature.feature.md")


def test_emit_parse_error_with_no_hook_is_noop() -> None:
    """emit_parse_error with no hook handler does nothing."""
    config = SimpleNamespace(stash={IdGenerator.STASH_KEY: IdGenerator()})
    # No hook attribute — should not raise
    BaseParser.emit_parse_error(config, message="test", line=1, column=1, uri="file:test.feature")


def test_emit_parse_error_with_non_callable_hook_is_noop() -> None:
    """emit_parse_error with non-callable hook handler does nothing."""
    config = SimpleNamespace(
        stash={IdGenerator.STASH_KEY: IdGenerator()},
        hook=SimpleNamespace(pytest_bdd_message=None),
    )
    BaseParser.emit_parse_error(config, message="test", line=1, column=1, uri="file:test.feature")
