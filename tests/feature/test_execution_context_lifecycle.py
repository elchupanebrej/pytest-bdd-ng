from __future__ import annotations


def test_each_scenario_gets_isolated_execution_context(testdir):
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
        Feature: Context isolation
            Scenario: First scenario
                Given shared step

            Scenario: Second scenario
                Given shared step
        """,
    )

    testdir.makepyfile(
        """
        from pytest_bdd import given, scenario

        def pytest_bdd_before_scenario(request, feature, scenario):
            context = request.execution_context
            assert context is not None
            request.config.session_context_ids = getattr(request.config, "session_context_ids", [])
            request.config.node_context_ids = getattr(request.config, "node_context_ids", [])
            request.config.session_context_ids.append(context.session.session_context_id)
            request.config.node_context_ids.append(context.context_id)

        def pytest_sessionfinish(session, exitstatus):
            session_ids = getattr(session.config, "session_context_ids", [])
            node_ids = getattr(session.config, "node_context_ids", [])
            assert len(set(session_ids)) == 1
            assert len(set(node_ids)) == 2

        @scenario('test.feature', 'First scenario')
        def test_first_scenario():
            pass

        @scenario('test.feature', 'Second scenario')
        def test_second_scenario():
            pass

        @given('shared step')
        def given_shared_step():
            return None
        """
    )

    result = testdir.runpytest("-q")
    result.assert_outcomes(passed=2)
