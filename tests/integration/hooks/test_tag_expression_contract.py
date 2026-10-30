"""Tag and mark hook expressions retain their different source grammars."""
import pytest

from pytest_cuke.compatibility.pytest import PYTEST83, ParseError
from pytest_cuke.tag_expression import GherkinTagExpression, MarksTagExpression, TagExpression

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("kind", "expression", "called"),
    [
        ("tag", "@smoke", True),
        ("tag", "smoke", False),
        ("tag", "@smoke and not @slow", True),
        ("mark", "smoke", True),
        ("mark", "smoke and not slow", True),
        ("mark", "slow", False),
        pytest.param(
            "mark", "browser(name='chrome')", True,
            marks=pytest.mark.skipif(not PYTEST83, reason="pytest marker kwargs require pytest 8.3+"),
        ),
    ],
)
def test_live_hook_expression_grammar(pytester, kind, expression, called):
    _make_consumer(pytester, kind, expression)
    result = pytester.runpytest("-q")
    result.assert_outcomes(passed=1)
    assert (pytester.path / "called.txt").exists() is called


@pytest.mark.parametrize(("kind", "expression"), [("mark", "@smoke"), ("mark", "smoke and"), ("tag", "@smoke and")])
def test_invalid_hook_expression_is_setup_error(pytester, kind, expression):
    _make_consumer(pytester, kind, expression)
    result = pytester.runpytest("-q")
    result.assert_outcomes(errors=1)
    expected = "SyntaxError" if kind == "mark" and ParseError is Exception else "ValueError"
    assert expected in result.stdout.str()
    assert not (pytester.path / "called.txt").exists()


def test_generic_expression_retains_normalized_api():
    assert TagExpression.parse("@smoke").evaluate(["smoke"])
    assert TagExpression.parse("smoke").evaluate(["@smoke"])
    assert not GherkinTagExpression.parse("@smoke").evaluate(["smoke"])
    assert GherkinTagExpression.parse("@smoke").evaluate(["@smoke"])
    assert MarksTagExpression.parse("smoke").evaluate(["smoke"])
    assert MarksTagExpression is not TagExpression
    assert GherkinTagExpression is not TagExpression


def _make_consumer(pytester, kind, expression):
    pytester.makeini("[pytest]\ncuke_features_dir = features\ncuke_parser = python\nmarkers =\n smoke\n browser\n")
    features = pytester.path / "features"
    features.mkdir()
    (features / "tag-expression.feature").write_text(
        "@smoke\nFeature: Expressions\n Scenario: One\n  When action\n", encoding="utf-8"
    )
    pytester.makeconftest(f'''
from pathlib import Path
import pytest
from pytest_cuke import when
from pytest_cuke.hook import before_{kind}

@before_{kind}({expression!r})
def observe(request):
    Path("called.txt").write_text("called")

def pytest_cuke_convert_tag_to_marks(tag):
    if tag == "smoke":
        return [pytest.mark.smoke, pytest.mark.browser(name="chrome")]

@when("action")
def action():
    pass
''')
