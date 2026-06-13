"""

Provide test hook run regression helpers.
"""

from __future__ import annotations


def test_mark_hooks_can_read_optional_run_without_breaking_existing_usage(testdir):
    """
    Verify mark hooks can read optional run without breaking existing usage.

    Test target:
        Ensure pytest hook lifecycle entrypoints trigger correctly and share state safely via config stash.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure pytest hook lifecycle entrypoints trigger correctly and
        share state safely via config stash., then the expected outcome is produced.
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
        @tag
        Feature: Hook context
            Scenario: Scenario
                When do work
        """,
    )
    testdir.makefile(
        ".ini",
        pytest="""
        [pytest]
        disable_feature_autoload = true
        markers =
            tag
        """,
    )
    testdir.makeconftest(
        """
        from pytest_bdd import when
        from pytest_bdd.hook import before_mark

        @before_mark('tag')
        def validate_run(request, run=None):
            assert request is not None
            assert run is not None

        @when('do work')
        def do_work():
            return None
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario('test.feature', 'Scenario')
        def test_scenario():
            pass
        """,
    )

    result = testdir.runpytest("-q")
    result.assert_outcomes(passed=1)
