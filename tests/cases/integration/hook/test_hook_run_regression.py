"""Provide test hook run regression helpers."""

from __future__ import annotations


def test_mark_hooks_can_read_optional_run_without_breaking_existing_usage(testdir):
    """Verify mark hooks can read optional run without breaking existing usage."""
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
