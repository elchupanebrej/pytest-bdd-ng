import ast

from pytest_bdd import given, parsers, then
from pytest_bdd.tag_expression import MarksTagExpression


@given(parsers.parse("Tag expression {expression}"), target_fixture="tag_expression")
def tag_expression(expression):
    expression = expression.strip('"').strip("'")
    return MarksTagExpression.parse(expression)


@given(parsers.parse("Complex boolean tag expression {expression}"), target_fixture="tag_expression")
def complex_tag_expression(expression):
    expression = expression.strip('"').strip("'")
    return MarksTagExpression.parse(expression)


class MockMark:
    def __init__(self, name):
        self.name = name


@then(parsers.parse("Tag expression evaluates to {result} for marks {marks}"))
def tag_expression_evaluates(tag_expression, result, marks):
    expected = result.lower() == "true"
    marks_clean = marks.strip('"').strip("'")
    marks_list = ast.literal_eval(marks_clean)
    mock_marks = [MockMark(m) for m in marks_list]
    from pytest_bdd.compatibility.pytest import MarkMatcher

    expr = tag_expression.expression
    matcher = MarkMatcher.from_markers(mock_marks)
    actual = expr.evaluate(matcher) if expr is not None else True
    assert actual == expected
