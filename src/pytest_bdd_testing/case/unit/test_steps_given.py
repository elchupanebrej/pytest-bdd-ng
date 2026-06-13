"""

Given tests.
"""

import pytest

pytestmark = [pytest.mark.unit]


def test_given_injection(testdir):
    """
    Verify given injection.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
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
