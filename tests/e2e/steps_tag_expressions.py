import ast

from pytest_bdd import given, parsers, then
from pytest_bdd.tag_expression import TagExpression


@given(parsers.parse("Tag expression {expression}"), target_fixture="tag_expression")
def tag_expression(expression):
    return TagExpression.parse(expression)


@given(parsers.parse("Complex boolean tag expression {expression}"), target_fixture="tag_expression")
def complex_tag_expression(expression):
    return TagExpression.parse(expression)


class MockMark:
    def __init__(self, name):
        self.name = name


@then(parsers.parse("Tag expression evaluates to {result} for marks {marks}"))
def tag_expression_evaluates(tag_expression, result, marks):
    expected = result.lower() == "true"
    marks_list = ast.literal_eval(marks)
    mock_marks = [MockMark(m) for m in marks_list]
    assert tag_expression.evaluate(mock_marks) == expected
