"""Unit tests for the _gherkin_go.parse() public API."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from pytest_bdd._gherkin_go._types import GherkinGoNotAvailable, GherkinParseError
from pytest_bdd.mimetype import Mimetype

VALID_GHERKIN_DOCUMENT = json.dumps(
    {
        "type": "GherkinDocument",
        "feature": {
            "type": "Feature",
            "language": "en",
            "keyword": "Feature",
            "name": "Test",
            "description": "",
            "children": [],
        },
    },
)

PARSE_ERROR_ARRAY = json.dumps(
    [{"source": {"uri": "", "location": {"line": 1, "column": 1}}, "message": "Parse error"}],
)


class TestParsePlainGherkin:
    def test_parses_valid_gherkin(self) -> None:
        with (
            patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
            patch("pytest_bdd._gherkin_go.parse_gherkin_document", return_value=VALID_GHERKIN_DOCUMENT),
        ):
            from pytest_bdd._gherkin_go import parse

            result = parse("Feature: Test\n  Scenario: Example", mimetype=Mimetype.gherkin_plain)
            assert result["type"] == "GherkinDocument"
            assert result["feature"]["name"] == "Test"

    def test_raises_on_parse_error(self) -> None:
        with (
            patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
            patch("pytest_bdd._gherkin_go.parse_gherkin_document", return_value=PARSE_ERROR_ARRAY),
        ):
            from pytest_bdd._gherkin_go import parse

            with pytest.raises(GherkinParseError, match="Parse error"):
                parse("invalid", mimetype=Mimetype.gherkin_plain)

    def test_raises_when_library_unavailable(self) -> None:
        with patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=False):
            from pytest_bdd._gherkin_go import parse

            with pytest.raises(GherkinGoNotAvailable, match="not available"):
                parse("Feature: Test", mimetype=Mimetype.gherkin_plain)


class TestParseMarkdownGherkin:
    def test_parses_markdown_via_go(self) -> None:
        with (
            patch("pytest_bdd._gherkin_go.gherkin_go_available", return_value=True),
            patch("pytest_bdd._gherkin_go.parse_gherkin_markdown", return_value=VALID_GHERKIN_DOCUMENT),
        ):
            from pytest_bdd._gherkin_go import parse

            result = parse("# Title\n```gherkin\nFeature: Test\n```", mimetype=Mimetype.gherkin_markdown)
            assert result["type"] == "GherkinDocument"


class TestBackendSelection:
    def test_should_use_go_backend_auto(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            from pytest_bdd._gherkin_go import should_use_go_backend

            assert should_use_go_backend() is True

    def test_should_use_go_backend_go(self) -> None:
        with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
            from pytest_bdd._gherkin_go import should_use_go_backend

            assert should_use_go_backend() is True

    def test_should_use_go_backend_python(self) -> None:
        with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
            from pytest_bdd._gherkin_go import should_use_go_backend

            assert should_use_go_backend() is False

    def test_strict_go_mode_true(self) -> None:
        with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "go"}):
            from pytest_bdd._gherkin_go import is_strict_go_mode

            assert is_strict_go_mode() is True

    def test_strict_go_mode_false_for_auto(self) -> None:
        with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "auto"}):
            from pytest_bdd._gherkin_go import is_strict_go_mode

            assert is_strict_go_mode() is False

    def test_strict_go_mode_false_for_python(self) -> None:
        with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "python"}):
            from pytest_bdd._gherkin_go import is_strict_go_mode

            assert is_strict_go_mode() is False

    def test_unknown_value_defaults_to_auto(self) -> None:
        with patch.dict("os.environ", {"PYTEST_BDD_GHERKIN_BACKEND": "invalid"}):
            from pytest_bdd._gherkin_go import should_use_go_backend

            assert should_use_go_backend() is True


class TestCrossBackendEquivalence:
    def test_documents_equivalent_strips_none(self) -> None:
        from pytest_bdd.collector_batch import _documents_equivalent

        go_doc = {"type": "GherkinDocument", "feature": None, "comments": []}
        python_doc = {"type": "GherkinDocument", "feature": None, "comments": [], "extra": None}
        assert _documents_equivalent(go_doc, python_doc) is True

    def test_documents_equivalent_ignores_ids(self) -> None:
        from pytest_bdd.collector_batch import _documents_equivalent

        go_doc = {"type": "GherkinDocument", "id": "go-123", "feature": {"name": "Test"}}
        python_doc = {"type": "GherkinDocument", "id": "py-456", "feature": {"name": "Test"}}
        assert _documents_equivalent(go_doc, python_doc) is True

    def test_documents_not_equivalent_different_content(self) -> None:
        from pytest_bdd.collector_batch import _documents_equivalent

        go_doc = {"type": "GherkinDocument", "feature": {"name": "Go"}}
        python_doc = {"type": "GherkinDocument", "feature": {"name": "Python"}}
        assert _documents_equivalent(go_doc, python_doc) is False
