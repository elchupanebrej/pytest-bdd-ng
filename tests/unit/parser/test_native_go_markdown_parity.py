"""Explicit Go selection must build the same model as Python for Markdown features."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from pytest_cuke._native_go._bridge import gherkin_go_available
from pytest_cuke.exceptions import FeatureConcreteParseError
from pytest_cuke.model.serialization import as_dict
from pytest_cuke.parser import MarkdownParser

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "markdown-fixtures"
MINIMAL_SHAPES = (
    FIXTURES / "heading-heavy.feature.md",
    FIXTURES / "fenced-example.feature.md",
    REPOSITORY_ROOT / "features" / "feature" / "description.feature.md",
)
CORPUS = sorted((REPOSITORY_ROOT / "features").glob("**/*.feature.md"))


def _without_ids(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_ids(child) for key, child in value.items() if key != "id"}
    if isinstance(value, list | tuple):
        return [_without_ids(child) for child in value]
    return value


def _models(fixture: Path) -> tuple[Any, Any]:
    content = fixture.read_text(encoding="utf-8")
    python_model = MarkdownParser().parse_text(content, parser_mode="python")
    native_model = MarkdownParser().parse_text(content, parser_mode="go")
    return _without_ids(as_dict(native_model)), _without_ids(as_dict(python_model))


def _require_native_parser() -> None:
    if not gherkin_go_available():
        pytest.skip("requires a host-built pytest-cuke wheel with the Go parser library")


@pytest.mark.parametrize("fixture", MINIMAL_SHAPES, ids=lambda path: path.name)
def test_explicit_go_matches_python_for_minimal_markdown_shapes(fixture: Path) -> None:
    _require_native_parser()

    native_model, python_model = _models(fixture)

    assert native_model == python_model


@pytest.mark.parametrize("fixture", CORPUS, ids=lambda path: path.relative_to(REPOSITORY_ROOT).as_posix())
def test_explicit_go_matches_python_for_the_markdown_corpus(fixture: Path) -> None:
    _require_native_parser()

    native_model, python_model = _models(fixture)

    assert native_model == python_model


def test_explicit_go_reports_the_same_markdown_error_as_python() -> None:
    _require_native_parser()
    malformed = "# Feature: Broken\n\n## Scenario: Broken\n\n* Given a step\n\n  ```gherkin\n  unterminated\n"

    errors = {}
    for mode in ("python", "go"):
        with pytest.raises(FeatureConcreteParseError) as error:
            MarkdownParser().parse_text(malformed, uri="broken.feature.md", parser_mode=mode)
        raised = error.value
        errors[mode] = (raised.parse_message, raised.line, raised.line_text, raised.source_uri, raised.column)

    assert errors["go"] == errors["python"]
