Feature: Session-owned scenario runtime integration
  An installed, autoloaded consumer can observe the active runtime context through
  both the existing pytest-cuke scenario hook and step fixture seam.

  Scenario: A scenario hook and step share one session run context
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from __future__ import annotations

      import json
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given, when


      _scenario_hook_observations = []


      @hookimpl
      def pytest_cuke_before_scenario(request, feature, scenario):
          run_context = request.getfixturevalue("run_context")
          _scenario_hook_observations.append(
              {
                  "scenario_name": scenario.name,
                  "run_context": run_context,
                  "scenario_run": run_context.active_scenario_run,
              }
          )


      @given("the scenario hook has observed the active runtime")
      def hook_observed_runtime(run_context):
          assert len(_scenario_hook_observations) == 1
          observation = _scenario_hook_observations[0]
          assert observation["run_context"] is run_context
          assert observation["scenario_run"] is run_context.active_scenario_run


      @when("I inspect the active scenario identity")
      def inspect_active_scenario_identity(run_context):
          observation = _scenario_hook_observations[0]
          scenario_run = run_context.active_scenario_run
          assert observation["run_context"] is run_context
          assert observation["scenario_run"] is scenario_run
          assert scenario_run is not None
          assert scenario_run.test_case_started_id

          Path("runtime-observation.json").write_text(
              json.dumps(
                  {
                      "scenario_name": observation["scenario_name"],
                      "hook_context_identity": id(observation["run_context"]),
                      "step_context_identity": id(run_context),
                      "hook_scenario_run_identity": id(observation["scenario_run"]),
                      "step_scenario_run_identity": id(scenario_run),
                      "scenario_run_id": scenario_run.run_id,
                      "test_case_started_id": scenario_run.test_case_started_id,
                  }
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/runtime.feature" contains:
      """gherkin
      Feature: Runtime context consumer
        Scenario: An autoloaded scenario observes its execution context
          Given the scenario hook has observed the active runtime
          When I inspect the active scenario identity
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer runtime observation "runtime-observation.json" should link to scenario "An autoloaded scenario observes its execution context" in Messages "messages.ndjson" and report "report.json"

  Scenario: Plain pytest receives a run context with no active BDD scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer directory "features" exists
    And consumer file "test_plain_runtime.py" contains:
      """python
      import json
      from pathlib import Path


      def test_plain_pytest_gets_inactive_bdd_runtime(run_context):
          assert run_context.active_feature_binding is None
          assert run_context.active_scenario_run is None
          assert run_context.status == "inactive"
          Path("plain-runtime-observation.json").write_text(
              json.dumps(
                  {
                      "active_feature_binding": run_context.active_feature_binding is not None,
                      "active_scenario_run": run_context.active_scenario_run is not None,
                      "status": run_context.status,
                  }
              ),
              encoding="utf-8",
          )
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And pytest output should include "1 passed"
    And consumer runtime snapshot "plain-runtime-observation.json" should show no active BDD scenario

  Scenario: A teardown failure is retained after active runtime references are cleared
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import fixture, hookimpl
      from pytest_cuke import given


      _run_context = None
      _scenario_nodeid = None


      @hookimpl
      def pytest_cuke_before_scenario(request, feature, scenario):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @fixture
      def fixture_with_failing_teardown():
          yield
          raise RuntimeError("runtime teardown failure sentinel")


      @given("the scenario uses a fixture with a failing teardown")
      def scenario_uses_failing_teardown(fixture_with_failing_teardown):
          pass


      @hookimpl(hookwrapper=True)
      def pytest_runtest_makereport(item, call):
          outcome = yield
          if call.when != "teardown" or item.nodeid != _scenario_nodeid:
              return

          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          Path("teardown-observation.json").write_text(
              json.dumps(
                  {
                      "active_feature_binding": _run_context.active_feature_binding is not None,
                      "active_scenario_run": _run_context.active_scenario_run is not None,
                      "scenario_history_found": scenario_run is not None,
                      "scenario_status": scenario_run.status if scenario_run is not None else None,
                      "active_step": (
                          scenario_run.current_step_run is not None if scenario_run is not None else None
                      ),
                      "exception_type": (
                          type(scenario_run.exception).__name__
                          if scenario_run is not None and scenario_run.exception is not None
                          else None
                      ),
                      "exception_message": (
                          str(scenario_run.exception)
                          if scenario_run is not None and scenario_run.exception is not None
                          else None
                      ),
                  }
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/teardown-runtime.feature" contains:
      """gherkin
      Feature: Runtime cleanup after teardown failure
        Scenario: A failed teardown leaves a closed root and inspectable history
          Given the scenario uses a fixture with a failing teardown
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 1
    And consumer runtime snapshot "teardown-observation.json" should retain the failed scenario after clearing active refs
