"""Provide test gherkin message reporter pytest90 regression helpers."""

from __future__ import annotations


def test_messages_reporter_avoids_old_style_teardown_warning_in_runtest_setup(testdir):
    """Verify messages reporter avoids old style teardown warning in runtest setup."""
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
