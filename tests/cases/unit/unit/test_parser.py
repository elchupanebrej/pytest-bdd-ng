"""Unit tests for Gherkin parser helpers."""

from __future__ import annotations

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
