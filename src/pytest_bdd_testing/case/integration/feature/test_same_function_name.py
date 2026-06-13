"""

Provide test same function name helpers.
"""


def test_when_function_name_same_as_step_name(testdir):
    """
    Verify when function name same as step name.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
        same_name="""\
            Feature: Function name same as step name
                Scenario: When function name same as step name
                    When something
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import when

        @when("something")
        def something():
            return "something"
        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
