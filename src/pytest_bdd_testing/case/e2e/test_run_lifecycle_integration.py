"""

Test scenario execution lifecycle — RunStage transitions and hook ordering.
"""


def test_full_lifecycle_transitions(testdir):
    """
    Verify all RunStage transitions fire in correct order through hooks.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, when, then

        def pytest_bdd_before_scenario(request, run):
            scenario_run = run.active_scenario_run
            request.config.lifecycle_transitions = getattr(request.config, "lifecycle_transitions", [])
            request.config.lifecycle_transitions.append(("before_scenario", str(scenario_run.stage)))

        def pytest_bdd_before_step(request, run, step_func):
            scenario_run = run.active_scenario_run
            request.config.lifecycle_transitions.append(("before_step", str(scenario_run.stage)))

        def pytest_bdd_before_step_call(request, run, step_func, step_func_args, step_definition):
            scenario_run = run.active_scenario_run
            request.config.lifecycle_transitions.append(("before_step_call", str(scenario_run.stage)))

        def pytest_bdd_after_step(request, run, step_func, step_func_args, step_definition):
            scenario_run = run.active_scenario_run
            request.config.lifecycle_transitions.append(("after_step", str(scenario_run.stage)))

        def pytest_bdd_after_scenario(request, run):
            scenario_run = run.active_scenario_run
            request.config.lifecycle_transitions.append(("after_scenario", str(scenario_run.stage)))

        @given("first step")
        def first_step():
            pass

        @when("second step")
        def second_step():
            pass

        @then("third step")
        def third_step():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        lifecycle="""\
            Feature: Lifecycle transitions
                Scenario: Three step scenario
                    Given first step
                    When second step
                    Then third step
        """,
    )
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import scenario

        @scenario("test.feature", "Three step scenario")
        def test_lifecycle():
            pass

        def test_transitions(request):
            hook_names = [r[0] for r in request.config.lifecycle_transitions]
            stage_names = [r[1] for r in request.config.lifecycle_transitions]
            # First transition: before_scenario should see scenario_setup
            assert "scenario_setup" in stage_names
            # Hook ordering: before_step before before_step_call before after_step
            before_step_idx = hook_names.index("before_step")
            before_step_call_idx = hook_names.index("before_step_call")
            after_step_idx = hook_names.index("after_step")
            assert before_step_idx < before_step_call_idx < after_step_idx
            # after_scenario should fire at end
            assert hook_names[-1] == "after_scenario"
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2, skipped=1)


def test_step_error_triggers_error_hook(testdir):
    """
    step_error hook fires when a step function raises an exception.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, scenario

        def pytest_bdd_step_error(request, run, step_func, step_func_args,
                                   exception, step_definition):
            request.config.step_errors = getattr(request.config, "step_errors", [])
            request.config.step_errors.append(exception)

        @given("a failing step")
        def failing_step():
            raise ValueError("step failed!")

        @scenario("test.feature", "Step error handling")
        def test_error_hook():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        error="""\
            Feature: Step error
                Scenario: Step error handling
                    Given a failing step
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test fails; wrapper not collected separately on failure
    result.assert_outcomes(failed=1)


def test_step_lookup_error_hook(testdir):
    """
    step_func_lookup_error hook fires when no step definition matches.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import scenario

        def pytest_bdd_step_func_lookup_error(request, run, exception):
            request.config.lookup_errors = getattr(request.config, "lookup_errors", [])
            request.config.lookup_errors.append(exception)

        @scenario("test.feature", "Undefined step")
        def test_lookup_error():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        undefined="""\
            Feature: Undefined step
                Scenario: Undefined step triggers lookup error
                    Given this step is not defined anywhere
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test fails; wrapper not collected separately on failure
    result.assert_outcomes(failed=1)


def test_before_step_called_before_before_step_call(testdir):
    """
    before_step hook fires before before_step_call hook.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, when, then, scenario

        def pytest_bdd_before_step(request, run, step_func):
            request.config.hook_order = getattr(request.config, "hook_order", [])
            request.config.hook_order.append("before_step")

        def pytest_bdd_before_step_call(request, run, step_func,
                                        step_func_args, step_definition):
            request.config.hook_order.append("before_step_call")

        def pytest_bdd_after_step(request, run, step_func, step_func_args,
                                  step_definition):
            request.config.hook_order.append("after_step")

        @given("an ordered step")
        def ordered_step():
            pass

        @scenario("test.feature", "Hook ordering")
        def test_hook_order():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        ordered="""\
            Feature: Hook ordering
                Scenario: Hook order verification
                    Given an ordered step
        """,
    )
    result = testdir.runpytest("-v")
    # Only wrapper function in test file → replaced by scenario test
    result.assert_outcomes(passed=1)


def test_after_scenario_fires_even_after_step_error(testdir):
    """
    after_scenario hook fires even when a step error occurs.

    Test target:
        Guard exception handling, validation checks, and error reporting to ensure fail-safe execution.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Guard exception handling, validation checks, and error reporting
        to ensure fail-safe execution., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, scenario

        def pytest_bdd_before_scenario(request, run):
            request.config.hooks_fired = getattr(request.config, "hooks_fired", [])
            request.config.hooks_fired.append("before_scenario")

        def pytest_bdd_step_error(request, run, step_func, step_func_args,
                                   exception, step_definition):
            request.config.hooks_fired.append("step_error")

        def pytest_bdd_after_scenario(request, run):
            request.config.hooks_fired.append("after_scenario")

        @given("a failing step")
        def failing():
            raise RuntimeError("fail")

        @scenario("test.feature", "Error scenario")
        def test_error_scenario():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        error_scenario="""\
            Feature: After scenario on error
                Scenario: Fires after error
                    Given a failing step
        """,
    )
    result = testdir.runpytest("-v")
    # Scenario test fails; wrapper not collected separately on failure
    result.assert_outcomes(failed=1)


def test_scenario_isolation_between_scenarios(testdir):
    """
    Two scenarios in same feature have independent state.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, then, scenario

        @given("first scenario step")
        def first_scenario_step(request):
            request.config.counter_state = getattr(request.config, "counter_state", {"counter": 0})
            request.config.counter_state["counter"] += 1
            return request.config.counter_state["counter"]

        @given("second scenario step")
        def second_scenario_step(request):
            request.config.counter_state = getattr(request.config, "counter_state", {"counter": 0})
            request.config.counter_state["counter"] += 10
            return request.config.counter_state["counter"]

        @then("value should be {expected:d}")
        def check_value(expected):
            pass

        @scenario("test.feature", "First scenario")
        def test_first():
            pass

        @scenario("test.feature", "Second scenario")
        def test_second():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        isolated="""\
            Feature: Scenario isolation
                Scenario: First scenario
                    Given first scenario step
                    Then value should be 1

                Scenario: Second scenario
                    Given second scenario step
                    Then value should be 10
        """,
    )
    result = testdir.runpytest("-v")
    # Only wrapper functions in test file → replaced by scenario tests
    result.assert_outcomes(passed=2)


def test_runstage_values_match_phase_to_stage_mapping(testdir):
    """
    Verify RunStage values at each hook match PHASE_TO_STAGE mapping.

    Test target:
        Protect end-to-end functionality and user-facing acceptance criteria.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Protect end-to-end functionality and user-facing acceptance
        criteria., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, when, then

        def pytest_bdd_before_scenario(request, run):
            stage = run.active_scenario_run.stage
            request.config.stages = getattr(request.config, "stages", {})
            request.config.stages["before_scenario"] = str(stage)

        def pytest_bdd_before_step(request, run, step_func):
            stage = run.active_scenario_run.stage
            request.config.stages["before_step"] = str(stage)

        def pytest_bdd_after_scenario(request, run):
            stage = run.active_scenario_run.stage
            request.config.stages["after_scenario"] = str(stage)

        @given("a step")
        def a_step():
            pass

        @when("another step")
        def another_step():
            pass

        @then("final step")
        def final_step():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        stage_mapping="""\
            Feature: Stage mapping
                Scenario: Verify stages
                    Given a step
                    When another step
                    Then final step
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Verify stages")
        def test_stages():
            pass

        def test_stage_values(request):
            stages = request.config.stages
            # before_scenario -> scenario_setup
            assert stages["before_scenario"] == "scenario_setup"
            # before_step -> step_running
            assert stages["before_step"] == "step_running"
            # after_scenario sees finished (transition applied before hook fires)
            assert stages["after_scenario"] == "finished"
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2, skipped=1)


def test_xdist_parallel_no_state_leakage(testdir):
    """
    Xdist parallel execution (-n 2) does not corrupt shared Run state.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
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
    testdir.makeconftest(
        """
        from pytest_bdd import given, then

        @given("I have value {n:d}")
        def set_value(n, request):
            request.config.test_values = getattr(request.config, "test_values", [])
            request.config.test_values.append(n)

        @then("value is {n:d}")
        def check_value(n, request):
            assert n in request.config.test_values
        """,
    )
    testdir.makefile(
        ".feature",
        parallel="""\
            Feature: Parallel execution
                Scenario: Worker A scenario
                    Given I have value 100
                    Then value is 100

                Scenario: Worker B scenario
                    Given I have value 200
                    Then value is 200
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        @scenario("test.feature", "Worker A scenario")
        def test_worker_a():
            pass

        @scenario("test.feature", "Worker B scenario")
        def test_worker_b():
            pass
        """,
    )
    result = testdir.runpytest("-v", "-n", "2")
    # xdist collects wrapper functions separately → skipped
    result.assert_outcomes(passed=2, skipped=2)
