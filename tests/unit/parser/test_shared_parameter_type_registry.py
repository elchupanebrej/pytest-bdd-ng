from __future__ import annotations


def test_shared_parameter_type_registry(testdir):
    testdir.makefile(
        ".feature",
        test_shared="""
Feature: Shared parameter type registry
    Scenario: Use custom parameter type in both expression types
        Given point (10, 20) defined via cucumber expression
        When point (30, 40) defined via cucumber regex
        Then points are recorded
""",
    )
    testdir.makeconftest(
        """
import pytest
from cucumber_expressions.parameter_type import ParameterType
from pytest_bdd import given, when, then
from pytest_bdd.parsers import cucumber_expression, cucumber_regular_expression

class Point:
    def __init__(self, x: int, y: int):
        self.x = int(x)
        self.y = int(y)

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

def parse_point(*args):
    if len(args) == 2:
        return Point(args[0], args[1])
    elif len(args) == 1:
        s = args[0].strip("()")
        x, y = s.split(",")
        return Point(x.strip(), y.strip())
    raise ValueError(f"Unexpected args: {args}")

@pytest.fixture
def parameter_type_registry(parameter_type_registry):
    parameter_type_registry.define_parameter_type(
        ParameterType(
            name="point",
            regexp=r"\\(\\d+,\\s*\\d+\\)",
            type=Point,
            transformer=parse_point,
            use_for_snippets=True,
            prefer_for_regexp_match=True,
        )
    )
    return parameter_type_registry

points = []

@given(cucumber_expression("point {point} defined via cucumber expression"), anonymous_group_names=["point"])
def given_point(point: Point):
    assert point == Point(10, 20)
    points.append(point)

@when(cucumber_regular_expression(r"point (?P<point>\\(\\d+,\\s*\\d+\\)) defined via cucumber regex"))
def when_point(point: Point):
    assert point == Point(30, 40)
    points.append(point)

@then("points are recorded")
def then_recorded():
    assert len(points) == 2
    assert points == [Point(10, 20), Point(30, 40)]
"""
    )
    result = testdir.runpytest_inprocess()
    result.assert_outcomes(passed=1)
