from __future__ import annotations


def test_session_execution_context_is_available_via_fixture_and_stash(testdir):
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
        Feature: Session context fixture
            Scenario: Access stash and fixture
                Given any step
        """,
    )

    testdir.makeconftest(
        """
        from pytest_bdd.plugin.scenario_runner.context_store import ExecutionContextStore

        def pytest_sessionstart(session):
            assert ExecutionContextStore.SESSION_CONTEXT_STASH_KEY in session.config.stash
            session_context = session.config.stash[ExecutionContextStore.SESSION_CONTEXT_STASH_KEY]
            assert session_context is not None
            session.config._session_context_id = id(session_context)

        def pytest_bdd_before_scenario(request, execution_context):
            session_context = request.getfixturevalue('session_execution_context')
            stash_context = request.config.stash[ExecutionContextStore.SESSION_CONTEXT_STASH_KEY]
            assert session_context is stash_context
            assert id(session_context) == request.config._session_context_id
        """
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
        """
    )

    result = testdir.runpytest("-q")
    result.assert_outcomes(passed=1)
