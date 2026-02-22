"""Scenario Outline tests."""

from textwrap import dedent

import pytest

from pytest_bdd.compatibility.pytest import assert_outcomes

pytestmark = [pytest.mark.e2e_deferred_conversion]


@pytest.fixture
def steps_conftest(testdir):
    testdir.makeconftest(
        dedent(
            # language=python
            """ \
                from pytest_bdd import parsers, given, when, then
            from pytest_bdd.util.toolz_test import dump_obj


            @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
            def start_cucumbers(start):
                assert isinstance(start, int)
                dump_obj(start)
                return {"start": start}


            @when(parsers.parse("I eat {eat:g} cucumbers"))
            def eat_cucumbers(start_cucumbers, eat):
                assert isinstance(eat, float)
                dump_obj(eat)
                start_cucumbers["eat"] = eat


            @then(parsers.parse("I should have {left} cucumbers"))
            def should_have_left_cucumbers(start_cucumbers, start, eat, left):
                assert isinstance(left, str)
                dump_obj(left)
                assert start - eat == int(left)
                assert start_cucumbers["start"] == start
                assert start_cucumbers["eat"] == eat
            """,
        ),
    )


def test_invalid_feature_parsing(
    testdir,
    steps_conftest,  # noqa: ARG001 fixture
):
    """Test invalid feature file parsing produces proper error message."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |   12  | 10  |   7  |
                    |    2  |  1  |
            """,
    )

    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines("*FeatureConcreteParseError*")
