from __future__ import annotations


def test_hook_callbacks_share_same_execution_context_reference(testdir):
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
        def pytest_bdd_before_scenario(request, feature, scenario):
            assert request.execution_context is not None
            assert feature.execution_context is not None
            assert scenario.execution_context is not None
            request.config.execution_context_ids = [id(request.execution_context)]

        def pytest_bdd_before_step(request, feature, scenario, step, step_func):
            assert step.execution_context is not None
            request.config.execution_context_ids.append(id(request.execution_context))

        def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args, step_definition):
            request.config.execution_context_ids.append(id(request.execution_context))

        def pytest_bdd_after_scenario(request, feature, scenario):
            request.config.execution_context_ids.append(id(request.execution_context))
            assert len(set(request.config.execution_context_ids)) == 1
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
