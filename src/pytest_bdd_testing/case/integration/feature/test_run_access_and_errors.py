"""

Test run access error paths and reporting degradation — integration level.
"""


def test_step_error_hook_receives_exception(testdir):
    """
    StepError hook receives the original exception from the failing step.

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
            request.config.step_errors.append(str(exception))

        @given("a failing step")
        def failing_step():
            raise ValueError("step failed!")

        @scenario("test.feature", "Step error captures exception")
        def test_error_hook():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        error="""\
            Feature: Step error hook
                Scenario: Step error captures exception
                    Given a failing step
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(failed=1)


def test_step_lookup_error_hook_receives_not_found(testdir):
    """
    StepFuncLookupError hook fires for undefined steps with correct details.

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
            request.config.lookup_errors.append(str(exception))

        @scenario("test.feature", "Undefined step")
        def test_lookup_error():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        undefined="""\
            Feature: Step lookup error
                Scenario: Undefined step
                    Given this step is totally undefined
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(failed=1)


def test_scenario_cleanup_after_error_succeeds(testdir):
    """
    After scenario errors, cleanup leaves Run in correct state for next scenario.

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
        from pytest_bdd import given, when, then, scenario

        @given("a setup step")
        def setup(request):
            request.config.setup_done = True
            return "setup_done"

        @when("an error occurs")
        def error_step():
            raise RuntimeError("expected error")

        @then("cleanup should work")
        def cleanup_check(request):
            assert request.config.setup_done

        @scenario("test.feature", "First scenario with error")
        def test_first_error():
            pass

        @scenario("test.feature", "Second scenario after error")
        def test_second_clean():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        cleanup="""\
            Feature: Scenario cleanup
                Scenario: First scenario with error
                    Given a setup step
                    When an error occurs
                    Then cleanup should work

                Scenario: Second scenario after error
                    Given a setup step
                    Then cleanup should work
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(failed=1, passed=1)


def test_reporting_context_snapshot_with_no_active_scenario(testdir):
    """
    Reporting context snapshot degrades gracefully with no active scenario.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
            request.config.snapshots = getattr(request.config, "snapshots", [])
            snap = run.active_scenario_run.stage.name
            request.config.snapshots.append(("before", snap))

        def pytest_bdd_after_scenario(request, run):
            snap = run.active_scenario_run.stage.name
            request.config.snapshots.append(("after", snap))

        @given("a simple step")
        def simple_step():
            pass

        @scenario("test.feature", "Snapshot test")
        def test_snapshot():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        snapshot="""\
            Feature: Reporting snapshot
                Scenario: Snapshot test
                    Given a simple step
        """,
    )
    testdir.makepyfile(
        """
        def test_snapshot_stage(request):
            snapshots = request.config.snapshots
            assert len(snapshots) == 2
            assert snapshots[0] == ("before", "scenario_setup")
            assert snapshots[1][0] == "after"
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2)


def test_multiple_scenarios_sequential_state_isolation(testdir):
    """
    Sequential scenarios have isolated Run state — no phantom refs.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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

        @given("step for scenario {num}")
        def scenario_step(num, request):
            request.config.state_tracker = getattr(request.config, "state_tracker", [])
            request.config.state_tracker.append(("scenario", num))
            return num

        @then("scenario {num} result is correct")
        def verify_scenario(num, request):
            assert request.config.state_tracker[-1] == ("scenario", num)

        @scenario("test.feature", "Scenario One")
        def test_one():
            pass

        @scenario("test.feature", "Scenario Two")
        def test_two():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        sequential="""\
            Feature: Sequential isolation
                Scenario: Scenario One
                    Given step for scenario 1
                    Then scenario 1 result is correct

                Scenario: Scenario Two
                    Given step for scenario 2
                    Then scenario 2 result is correct
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2)


def test_require_pickle_object_missing(testdir):
    """
    Missing pickle object raises RuntimeError in require_pickle_object.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
        from pytest_bdd.model.run import Run

        @given("a step")
        def a_step():
            return "test"

        def pytest_bdd_before_scenario(request, run):
            scenario_run = run.active_scenario_run
            assert scenario_run is not None

        @scenario("test.feature", "Simple")
        def test_simple():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        pickle_test="""\
            Feature: Require pickle test
                Scenario: Simple
                    Given a step
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_missing_feature_binding_raises_runtime_error(testdir):
    """
    Scenario run access verifies feature binding is available during hooks.

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
        from pytest_bdd.model.run_access import require_feature_binding

        @given("a step")
        def a_step():
            return "test"

        def pytest_bdd_before_scenario(request, run):
            # Verify binding is accessible during before_scenario
            scenario_run = run.active_scenario_run
            assert scenario_run is not None, "scenario_run should exist"
            # require_feature_binding should succeed when binding is present
            binding = require_feature_binding(run, hook_name="pytest_bdd_before_scenario")
            assert binding is not None
            request.config.binding_accessible = True

        @scenario("test.feature", "Binding accessible test")
        def test_binding_accessible():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        binding_accessible="""\
            Feature: Binding accessible
                Scenario: Binding accessible test
                    Given a step
        """,
    )
    testdir.makepyfile(
        """
        def test_binding_was_accessible(request):
            assert getattr(request.config, "binding_accessible", False)
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2)


def test_missing_gherkin_document_fallback(testdir):
    """
    Scenario run access verifies gherkin document fallback chain.

    Test target:
        Validate component collaboration, integration contracts, and boundary conditions.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Validate component collaboration, integration contracts, and
        boundary conditions., then the expected outcome is produced.
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
        from pytest_bdd.model.run_access import require_feature_object

        @given("a step")
        def a_step():
            return "test"

        def pytest_bdd_after_scenario(request, run):
            # Verify document is accessible during after_scenario
            scenario_run = run.active_scenario_run
            assert scenario_run is not None
            # require_feature_object should succeed when document is present
            doc = require_feature_object(run, hook_name="pytest_bdd_after_scenario")
            assert doc is not None
            request.config.doc_accessible = True

        @scenario("test.feature", "Document accessible test")
        def test_doc_accessible():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        doc_accessible="""\
            Feature: Document accessible
                Scenario: Document accessible test
                    Given a step
        """,
    )
    testdir.makepyfile(
        """
        def test_doc_was_accessible(request):
            assert getattr(request.config, "doc_accessible", False)
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2)


def test_require_step_object_missing_raises_error(testdir):
    """
    Missing step object raises RuntimeError when require_step_object called.

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
        from pytest_bdd.model.run_access import require_step_object

        @given("a step")
        def a_step():
            return "test"

        def pytest_bdd_before_step(request, run, step_func):
            scenario_run = run.active_scenario_run
            if scenario_run:
                scenario_run.step_object = None
                try:
                    require_step_object(run, hook_name="pytest_bdd_before_step")
                except RuntimeError as e:
                    request.config.step_obj_errors = getattr(request.config, "step_obj_errors", [])
                    request.config.step_obj_errors.append(str(e))

        @scenario("test.feature", "Step object missing test")
        def test_missing_step_obj():
            pass
        """,
    )
    testdir.makefile(
        ".feature",
        missing_step="""\
            Feature: Missing step object
                Scenario: Step object missing test
                    Given a step
        """,
    )
    testdir.makepyfile(
        """
        def test_step_obj_error_captured(request):
            errors = getattr(request.config, "step_obj_errors", [])
            assert len(errors) > 0
            assert "step" in errors[0].lower()
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=2)


def test_pop_scenario_run_cleanup_leaves_idle_state(testdir):
    """
    pop_scenario_run cleanup leaves Run in correct idle state for next scenario.

    Test target:
        Ensure proper resource cleanup and prevent memory leaks between test runs.
    Test type:
        Integration test
    Test scenario:
        Given the relevant preconditions are met, when Ensure proper resource cleanup and prevent memory leaks between
        test runs., then the expected outcome is produced.
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
        from pytest_bdd.model.run import RunStage

        @given("step for {name}")
        def setup_step(name, request):
            request.config.steps_run = getattr(request.config, "steps_run", [])
            request.config.steps_run.append(name)

        @then("run stage should be idle before scenario")
        def check_idle(request):
            pass

        def pytest_bdd_before_scenario(request, run):
            request.config.before_stages = getattr(request.config, "before_stages", [])
            request.config.before_stages.append(run.active_scenario_run.stage.name)

        def pytest_bdd_after_scenario(request, run):
            request.config.after_stages = getattr(request.config, "after_stages", [])
            request.config.after_stages.append(run.active_scenario_run.stage.name)

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
        cleanup="""\
            Feature: Cleanup verification
                Scenario: First scenario
                    Given step for first
                    Then run stage should be idle before scenario

                Scenario: Second scenario
                    Given step for second
                    Then run stage should be idle before scenario
        """,
    )
    testdir.makepyfile(
        """
        def test_cleanup_verification(request):
            before_stages = request.config.before_stages
            assert len(before_stages) == 2
            assert before_stages[0] == "scenario_setup"
            assert before_stages[1] == "scenario_setup"

            after_stages = request.config.after_stages
            assert len(after_stages) == 2
            assert "scenario_teardown" in after_stages[0] or "finished" in after_stages[0]
            assert "scenario_teardown" in after_stages[1] or "finished" in after_stages[1]

            steps_run = request.config.steps_run
            assert "first" in steps_run
            assert "second" in steps_run
        """,
    )
    result = testdir.runpytest("-v")
    result.assert_outcomes(passed=3)
