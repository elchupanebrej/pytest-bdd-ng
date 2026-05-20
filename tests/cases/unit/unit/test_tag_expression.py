"""Unit tests for tag expression helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_bdd.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpressionParser

pytestmark = [pytest.mark.unit]


def test_gherkin_expression_matches_present_tag() -> None:
    """Gherkin tag expression matches a present tag."""
    expression = GherkinTagExpression.parse("@foo")
    mark = SimpleNamespace(name="@foo")

    assert expression.evaluate([mark]) is True


def test_gherkin_expression_rejects_missing_tag() -> None:
    """Gherkin tag expression rejects a missing tag."""
    expression = GherkinTagExpression.parse("@foo")
    mark = SimpleNamespace(name="@bar")

    assert expression.evaluate([mark]) is False


def test_gherkin_expression_supports_negation() -> None:
    """Gherkin tag expression supports negation."""
    expression = GherkinTagExpression.parse("not @foo")
    mark = SimpleNamespace(name="@bar")

    assert expression.evaluate([mark]) is True


def test_gherkin_expression_supports_unicode_tag_names() -> None:
    """Gherkin tag expression supports unicode tag names."""
    expression = GherkinTagExpression.parse("@café")
    mark = SimpleNamespace(name="@café")

    assert expression.evaluate([mark]) is True


def test_gherkin_expression_wraps_trailing_operator_error() -> None:
    """Gherkin parser wraps trailing operator errors as ValueError."""
    with pytest.raises(ValueError, match="Unable parse tag expression"):
        GherkinTagExpression.parse("@foo and")


def test_raw_tag_expression_parser_empty_expression_matches_everything() -> None:
    """Raw cucumber parser treats an empty tag expression as match-all."""
    expression = TagExpressionParser.parse("")

    assert expression.evaluate([]) is True


def test_marks_expression_empty_matches_everything() -> None:
    """Empty pytest mark expression matches any mark set."""
    expression = MarksTagExpression.parse("")

    assert expression.evaluate([]) is True


def test_marks_expression_rejects_invalid_expression() -> None:
    """Invalid pytest mark expression raises parser syntax error."""
    with pytest.raises(SyntaxError):
        MarksTagExpression.parse("foo and")
