"""

Integration coverage for tag expression evaluation without feature-file parsing.
"""

from __future__ import annotations

import pytest
from attrs import define

from pytest_bdd.tag_expression import MarksTagExpression

pytestmark = [pytest.mark.unit]


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
    """
    Test target:
    Enforce tag filtering semantics to select and execute the correct subset of BDD scenarios.
    Test type:
    Unit test
    Test scenario:
    Given the relevant preconditions are met, when Enforce tag filtering semantics to select and execute the correct
        subset of BDD scenarios., then the expected outcome is produced.
    BDD reference:
    None
    Fixtures:
    - None
    Mocks:
    - None
    Side effects:
    None
    Reduction:
    Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
    Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
    All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
    Covers a distinct code path not exercised by any sibling test.
    Test quality score:
    #test-eval:isolation=5
    #test-eval:determinism=5
    #test-eval:setup_complexity=1
    #test-eval:assertions_clarity=5
    """
    assert MarksTagExpression.parse(expression).evaluate([Mark(mark) for mark in marks]) is expected
