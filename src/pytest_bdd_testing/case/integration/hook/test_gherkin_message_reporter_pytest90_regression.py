"""

Provide test gherkin message reporter pytest90 regression helpers.
"""

from __future__ import annotations


def test_messages_reporter_avoids_old_style_teardown_warning_in_runtest_setup(testdir):
    """
    Verify messages reporter avoids old style teardown warning in runtest setup.

    Test target:
        Verify Cucumber Messages protocol compliance to support external reporting tools and IDE bindings.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Verify Cucumber Messages protocol compliance to support external
        reporting tools and IDE bindings., then the expected outcome is produced.
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
        test="""
        Feature: Message reporting
            Scenario: Simple scenario
                Given a passing step
        """,
    )
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        disable_feature_autoload = true
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import given

        @given("a passing step")
        def passing_step():
            return None
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Simple scenario")
        def test_simple_scenario():
            pass
        """,
    )

    warnings_args = []
    try:
        import pluggy

        if hasattr(pluggy, "PluggyTeardownRaisedWarning"):
            warnings_args = ["-W", "error::pluggy.PluggyTeardownRaisedWarning"]
    except ImportError:
        pass

    result = testdir.runpytest_subprocess(
        *warnings_args,
        f"--messages-ndjson={testdir.tmpdir.join('../messages.ndjson')}",
        "-q",
    )

    result.assert_outcomes(passed=1)
    if warnings_args:
        assert "PluggyTeardownRaisedWarning" not in result.stdout.str()
