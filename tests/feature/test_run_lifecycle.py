from __future__ import annotations


def test_each_scenario_gets_isolated_scenario_run(testdir):
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

        def pytest_bdd_before_scenario(request, run):
            context = run.active_scenario_run
            assert context is not None
            request.config.run_context_ids = getattr(request.config, "run_context_ids", [])
            request.config.node_context_ids = getattr(request.config, "node_context_ids", [])
            request.config.run_context_ids.append(context.run.run_context_id)
            request.config.node_context_ids.append(context.context_id)

        def pytest_sessionfinish(session, exitstatus):
            run_ids = getattr(session.config, "run_context_ids", [])
            node_ids = getattr(session.config, "node_context_ids", [])
            assert len(set(run_ids)) == 1
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
