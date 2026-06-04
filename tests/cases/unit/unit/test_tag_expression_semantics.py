"""Integration coverage for tag expression evaluation without feature-file parsing."""

from __future__ import annotations

import pytest
from attrs import define

from pytest_bdd.tag_expression import MarksTagExpression


@define
class Mark:
    name: str


@pytest.mark.parametrize(
    ("expression", "marks", "expected"),
    [
        ("smoke and login", ["smoke", "login"], True),
        ("smoke and login", ["smoke", "slow"], False),
        ("smoke or slow", ["smoke", "login"], True),
        ("smoke or slow", ["slow", "login"], True),
        ("smoke or slow", ["login", "regression"], False),
        ("smoke and not slow", ["smoke", "login"], True),
        ("smoke and not slow", ["smoke", "slow"], False),
        ("(smoke or regression) and not slow", ["smoke", "login"], True),
        ("(smoke or regression) and not slow", ["regression"], True),
        ("(smoke or regression) and not slow", ["smoke", "slow"], False),
        ("", ["smoke"], True),
        ("", ["slow"], True),
        ("", [], True),
        ("smoke", ["smoke", "login"], True),
        ("smoke", ["slow", "login"], False),
        ("smoke and login and regression", ["smoke", "login", "regression"], True),
        ("smoke and login and regression", ["smoke", "login"], False),
        ("((smoke and not slow) or (login and not slow)) and regression", ["smoke", "regression"], True),
        ("((smoke and not slow) or (login and not slow)) and regression", ["login", "regression"], True),
        ("((smoke and not slow) or (login and not slow)) and regression", ["smoke", "slow", "regression"], False),
    ],
)
def test_tag_expression_evaluates_marks(expression: str, marks: list[str], expected) -> None:
    assert MarksTagExpression.parse(expression).evaluate([Mark(mark) for mark in marks]) is expected
