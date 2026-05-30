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
    with pytest.raises((ValueError, SyntaxError)):
        MarksTagExpression.parse("foo and")


def test_gherkin_expression_evaluates_or_expression() -> None:
    """Gherkin tag expression with OR evaluates true when one tag matches."""
    expression = GherkinTagExpression.parse("@foo or @bar")
    mark = SimpleNamespace(name="@foo")

    assert expression.evaluate([mark]) is True


def test_gherkin_expression_and_rejects_partial_match() -> None:
    """Gherkin tag expression with AND rejects when only one tag matches."""
    expression = GherkinTagExpression.parse("@foo and @bar")
    mark = SimpleNamespace(name="@foo")

    assert expression.evaluate([mark]) is False


def test_gherkin_expression_and_accepts_full_match() -> None:
    """Gherkin tag expression with AND accepts two matching marks."""
    expression = GherkinTagExpression.parse("@foo and @bar")

    assert expression.evaluate([SimpleNamespace(name="@foo"), SimpleNamespace(name="@bar")]) is True


def test_gherkin_expression_empty_tags_evaluates_false() -> None:
    """Gherkin expression evaluates false with empty mark list when expression is non-empty."""
    expression = GherkinTagExpression.parse("@foo")

    assert expression.evaluate([]) is False


def test_gherkin_expression_not_with_absent_tag() -> None:
    """Gherkin NOT expression accepts when tag is absent."""
    expression = GherkinTagExpression.parse("not @foo")

    assert expression.evaluate([]) is True


def test_gherkin_expression_empty_parses_and_matches_all() -> None:
    """Empty gherkin expression matches all marks."""
    expression = GherkinTagExpression.parse("")

    assert expression.evaluate([SimpleNamespace(name="@anything")]) is True


def test_marks_expression_with_single_mark_matches() -> None:
    """Pytest mark expression matches when mark is present."""
    expression = MarksTagExpression.parse("unit")
    mark = SimpleNamespace(name="unit")

    assert expression.evaluate([mark]) is True


def test_marks_expression_with_single_mark_rejects() -> None:
    """Pytest mark expression rejects when mark is absent."""
    expression = MarksTagExpression.parse("unit")
    mark = SimpleNamespace(name="integration")

    assert expression.evaluate([mark]) is False


def test_marks_expression_not_negation() -> None:
    """Pytest mark expression supports NOT negation."""
    expression = MarksTagExpression.parse("not unit")
    mark = SimpleNamespace(name="integration")

    assert expression.evaluate([mark]) is True


def test_marks_expression_and_syntax() -> None:
    """Pytest mark expression supports AND syntax."""
    expression = MarksTagExpression.parse("unit and slow")
    marks = [SimpleNamespace(name="unit"), SimpleNamespace(name="slow")]

    assert expression.evaluate(marks) is True


def test_gherkin_expression_unicode_negation() -> None:
    """Gherkin expression with unicode and negation."""
    expression = GherkinTagExpression.parse("not @café")
    mark = SimpleNamespace(name="@latte")

    assert expression.evaluate([mark]) is True


def test_raw_cucumber_parser_with_simple_tag() -> None:
    """Raw cucumber parser evaluates simple tag expressions."""
    expression = TagExpressionParser.parse("@foo")

    assert expression.evaluate(["@foo"]) is True
    assert expression.evaluate(["@bar"]) is False
