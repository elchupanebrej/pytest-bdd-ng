from __future__ import annotations

import pytest

from pytest_bdd.model.tag import Tag
from pytest_bdd.tag_expression import TagExpression, parse_tag_expression


def test_tag_expression_empty_and_whitespace() -> None:
    expr = parse_tag_expression("")
    assert expr.evaluate([]) is True
    assert expr.evaluate(["smoke"]) is True

    expr_ws = TagExpression.parse("   ")
    assert expr_ws.evaluate([]) is True
    assert expr_ws.evaluate(["@slow"]) is True


def test_tag_expression_single_tag() -> None:
    expr = parse_tag_expression("@smoke")
    assert expr.evaluate(["@smoke"]) is True
    assert expr.evaluate(["smoke"]) is True
    assert expr.evaluate([Tag(name="@smoke")]) is True
    assert expr.evaluate(["other"]) is False
    assert expr.evaluate([]) is False


def test_tag_expression_boolean_operators() -> None:
    expr_and = parse_tag_expression("@smoke and @fast")
    assert expr_and.evaluate(["smoke", "fast"]) is True
    assert expr_and.evaluate(["smoke"]) is False

    expr_or = parse_tag_expression("@smoke or @fast")
    assert expr_or.evaluate(["smoke"]) is True
    assert expr_or.evaluate(["fast"]) is True
    assert expr_or.evaluate(["slow"]) is False

    expr_not = parse_tag_expression("not @slow")
    assert expr_not.evaluate(["fast"]) is True
    assert expr_not.evaluate(["slow"]) is False


def test_tag_expression_complex_nested() -> None:
    expr = parse_tag_expression("(@smoke or @unit) and not @slow")
    assert expr.evaluate(["smoke", "fast"]) is True
    assert expr.evaluate(["unit"]) is True
    assert expr.evaluate(["smoke", "slow"]) is False
    assert expr.evaluate(["other"]) is False


def test_tag_expression_syntax_error() -> None:
    with pytest.raises(ValueError, match=r"Unable.*parse"):
        parse_tag_expression("(@smoke and")
