"""Given tests."""

import pytest

pytestmark = [pytest.mark.unit]


def test_given_injection(testdir):
    """Verify given injection."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        given="""\
            Feature: Given
                Scenario: Test given fixture injection
                    Given I have injecting given
                    Then foo should be "injected foo"
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, then

        @given("I have injecting given", target_fixture="foo")
        def injecting_given():
            return "injected foo"

        @then('foo should be "injected foo"')
        def foo_is_injected_foo(foo):
            assert foo == "injected foo"

        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
