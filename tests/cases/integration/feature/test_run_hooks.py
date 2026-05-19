"""Provide test run hooks helpers."""

from __future__ import annotations


def test_hook_callbacks_share_same_scenario_run_reference(testdir):
    """Verify hook callbacks share same scenario run reference."""
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
            scenario_run = run.active_scenario_run
            gherkin_document = scenario_run.gherkin_document
            pickle = scenario_run.pickle
            assert gherkin_document.feature.name == "Context identity"
            assert pickle.name == "Shared context reference"
            assert not hasattr(gherkin_document, "scenario_run")
            assert not hasattr(pickle, "scenario_run")
            request.config.scenario_run_ids = [id(scenario_run)]

        def pytest_bdd_before_step(request, run, step_func):
            scenario_run = run.active_scenario_run
            step = scenario_run.step_object
            assert step.text in {"first step", "second step"}
            assert not hasattr(step, "scenario_run")
            assert scenario_run.step_run.text == step.text
            request.config.scenario_run_ids.append(id(scenario_run))

        def pytest_bdd_after_step(
            request,
            run,
            step_func,
            step_func_args,
            step_definition,
        ):
            scenario_run = run.active_scenario_run
            assert scenario_run.step_run.parameters == {}
            request.config.scenario_run_ids.append(id(scenario_run))

        def pytest_bdd_after_scenario(request, run):
            scenario_run = run.active_scenario_run
            assert scenario_run.active_set.scenario.is_active is False
            request.config.scenario_run_ids.append(id(scenario_run))
            assert len(set(request.config.scenario_run_ids)) == 1
        """,
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
        """,
    )

    result = testdir.runpytest("-q")
    result.assert_outcomes(passed=1)
