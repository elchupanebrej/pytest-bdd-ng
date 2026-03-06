from __future__ import annotations


def test_hook_callbacks_share_same_scenario_run_reference(testdir):
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
        Feature: Context identity
            Scenario: Shared context reference
                Given first step
                When second step
        """,
    )

    testdir.makeconftest(
        """
        def pytest_bdd_before_scenario(request, run):
            assert run.active_scenario_run is not None
            gherkin_document = run.active_scenario_run.gherkin_document
            pickle = run.active_scenario_run.pickle
            assert gherkin_document is not None
            assert pickle is not None
            assert not hasattr(gherkin_document, "scenario_run")
            assert not hasattr(pickle, "scenario_run")
            request.config.scenario_run_ids = [id(run.active_scenario_run)]

        def pytest_bdd_before_step(request, run, step_func):
            step = run.active_scenario_run.step_object
            assert step is not None
            assert not hasattr(step, "scenario_run")
            request.config.scenario_run_ids.append(id(run.active_scenario_run))

        def pytest_bdd_after_step(
            request,
            run,
            step_func,
            step_func_args,
            step_definition,
        ):
            request.config.scenario_run_ids.append(id(run.active_scenario_run))

        def pytest_bdd_after_scenario(request, run):
            request.config.scenario_run_ids.append(id(run.active_scenario_run))
            assert len(set(request.config.scenario_run_ids)) == 1
        """
    )

    testdir.makepyfile(
        """
        from pytest_bdd import given, scenario, when

        @scenario('test.feature', 'Shared context reference')
        def test_shared_context_reference():
            pass

        @given('first step')
        def given_first_step():
            return None

        @when('second step')
        def when_second_step():
            return None
        """
    )

    result = testdir.runpytest("-q")
    result.assert_outcomes(passed=1)
