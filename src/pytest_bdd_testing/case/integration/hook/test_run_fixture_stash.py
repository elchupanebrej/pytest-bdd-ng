"""

Provide test run fixture stash helpers.
"""

from __future__ import annotations


def test_run_context_is_available_via_fixture_and_stash(testdir):
    """
    Verify run context is available via fixture and stash.

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
        ".ini",
        pytest="""
        [pytest]
        disable_feature_autoload = true
        """,
    )

    testdir.makefile(
        ".feature",
        test="""
        Feature: Run context fixture
            Scenario: Access stash and fixture
                Given any step
        """,
    )

    testdir.makeconftest(
        """
        from pytest_bdd.model.run import Run

        def pytest_sessionstart(session):
            assert Run.STASH_KEY in session.config.stash
            run_context = session.config.stash[Run.STASH_KEY]
            assert run_context is not None
            session.config._run_id = id(run_context)

        def pytest_bdd_before_scenario(request, run):
            run_context = request.getfixturevalue('run_context')
            stash_run = request.config.stash[Run.STASH_KEY]
            assert run_context is stash_run
            assert run is stash_run
            assert id(run_context) == request.config._run_id
        """,
    )

    testdir.makepyfile(
        """
        from pytest_bdd import given, scenario

        @scenario('test.feature', 'Access stash and fixture')
        def test_access_stash_and_fixture():
            pass

        @given('any step')
        def any_step():
            return None
        """,
    )

    result = testdir.runpytest("-q")
    result.assert_outcomes(passed=1)
