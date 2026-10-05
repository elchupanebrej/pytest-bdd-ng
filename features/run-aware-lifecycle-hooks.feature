Feature: Run-aware lifecycle hooks
  Installed pytest-cuke consumers can inspect the active scenario and step through
  the session-owned run context while lifecycle transitions are delivered.

  Scenario: Successful lifecycle hooks expose ordered run context
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer registers the run-aware lifecycle extension plugin
    And consumer file "features/run-aware-lifecycle.feature" contains:
      """gherkin
      Feature: Run-aware lifecycle consumer
        Scenario: Default dispatcher and caller fallbacks
          Given the first run-aware step records "alpha"
          When the next run-aware step records "beta"
          Then the last run-aware step records "omega"

        Scenario: Custom dispatcher invokes run-step and caller
          Given the first run-aware step records "custom-start"
          When the custom caller step records "custom-middle"
          Then the last run-aware step records "custom-end"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer run-aware hook artifact "run-aware-master.jsonl" should show successful run transitions

  Scenario: Body, lookup, and hook failures remain distinct and release context
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer registers the run-aware lifecycle extension plugin
    And consumer file "features/run-aware-failures.feature" contains:
      """gherkin
      Feature: Run-aware failure consumer
        Scenario: Body failure remains a step error
          When the run-aware body raises "body failure sentinel"

        Scenario: Replacement callable failure preserves hook payload
          When a replaceable run-aware step receives "callable payload sentinel"

        Scenario: Lookup failure remains a lookup error
          When an undefined run-aware operation occurs

        Scenario: Hook failure is cleaned up
          When the observer hook raises

        Scenario: Fresh scenario starts without prior steps
          Given the first run-aware step records "fresh-start"
          When the next run-aware step records "fresh-middle"
          Then the last run-aware step records "fresh-end"
      """
    And consumer file "test_runtime_cleanup.py" contains:
      """python
      import json
      from pathlib import Path


      def test_run_context_is_released_after_scenarios(run_context):
          observation = {
              "active_feature": run_context.active_feature_binding is not None,
              "active_scenario": run_context.active_scenario_run is not None,
              "feature": getattr(run_context, "feature", None),
              "scenario": getattr(run_context, "scenario", None),
              "step": getattr(run_context, "step", None),
              "previous_step": getattr(run_context, "previous_step", None),
              "stage": run_context.stage,
              "hook_phase": run_context.hook_phase,
              "status": run_context.status,
          }
          for key in ("feature", "scenario", "step", "previous_step"):
              value = observation[key]
              observation[key] = getattr(value, "name", value)
          Path("run-aware-cleanup.json").write_text(json.dumps(observation, sort_keys=True), encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with code 1
    And consumer run-aware hook artifact "run-aware-master.jsonl" should distinguish failures and cleanup

  Scenario: Two pytest.main sessions receive separate run contexts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer registers the run-aware lifecycle extension plugin
    And consumer file "features/same-process.feature" contains:
      """gherkin
      Feature: Run-aware same-process sessions
        Scenario: First pytest.main session starts clean
          Given the first run-aware step records "session-one"

        Scenario: Second pytest.main session starts clean
          Given the first run-aware step records "session-two"
      """
    When I run installed pytest twice in one process with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q -k First" and then "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q -k Second"
    Then consumer repeated pytest sessions should exit with codes "0,0"
    And consumer run-aware observations should isolate two pytest.main sessions

  Scenario: Xdist workers own separate run contexts
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the installed consumer registers the run-aware lifecycle extension plugin
    And consumer file "features/xdist-run-context.feature" contains:
      """gherkin
      Feature: Run-aware xdist consumer
        Scenario: First xdist worker scenario
          Given the first run-aware step records "worker-one"

        Scenario: Second xdist worker scenario
          Given the first run-aware step records "worker-two"
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-summary -q -n2 --dist=each"
    Then pytest should exit with code 0
    And consumer run-aware xdist artifacts should show isolated contexts on two workers

  Scenario: The checked-in run-aware hooks example runs from an installed consumer
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And Copy path from "examples/run-aware-hooks" to test path "run-aware-hooks"
    And the staged E2E example "run-aware-hooks" is copied to the installed consumer
    When I run installed pytest from consumer directory "run-aware-hooks" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 3 passed scenarios
    And consumer run-aware example artifact "run-aware-hooks/run-aware-observations.jsonl" should show all scenarios, lifecycle context, and the attachment
