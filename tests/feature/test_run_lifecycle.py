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
        # language=python
        """
        from pytest_bdd import given, scenario

        def pytest_bdd_before_scenario(request, run):
            scenario_run = run.active_scenario_run
            request.config.run_ids = getattr(request.config, "run_ids", [])
            request.config.scenario_ids = getattr(request.config, "scenario_ids", [])
            request.config.feature_names = getattr(request.config, "feature_names", [])
            request.config.run_ids.append(scenario_run.run.id)
            request.config.scenario_ids.append(scenario_run.id)
            request.config.feature_names.append(scenario_run.gherkin_document.feature.name)

        def pytest_sessionfinish(session, exitstatus):
            run_ids = getattr(session.config, "run_ids", [])
            node_ids = getattr(session.config, "scenario_ids", [])
            feature_names = getattr(session.config, "feature_names", [])
            assert len(set(run_ids)) == 1
            assert len(set(node_ids)) == 2
            assert feature_names == ["Context isolation", "Context isolation"]

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
