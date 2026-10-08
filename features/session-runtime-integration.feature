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
      def pytest_cuke_before_scenario(request, run):
          run_context = request.getfixturevalue("run_context")
          _scenario_hook_observations.append(
              {
                  "scenario_name": run.scenario.name,
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
                      "run_id": run_context.run_id,
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer runtime observation "runtime-observation.json" should link to scenario "An autoloaded scenario observes its execution context" in Messages "messages.ndjson" and report "report.json"
    And consumer runtime artifact "runtime-observation.json" should match the run ID in Messages "messages.ndjson"

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
      def pytest_cuke_before_scenario(request, run):
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

  Scenario: Sequential ordinary scenarios and outline rows have isolated runtime state
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given, parsers, then, when


      _phase_snapshots = {}


      def _snapshot(run_context, hook_phase):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          _phase_snapshots.setdefault(scenario_run.nodeid, []).append(
              {
                  "hook_phase": hook_phase,
                  "runtime_hook_phase": run_context.hook_phase,
                  "transition_index": run_context.transition_index,
                  "stage": run_context.stage,
                  "status": run_context.status,
                  "active_scenario": run_context.active_scenario_run is scenario_run,
                  "scenario_identity": id(scenario_run),
                  "scenario_status": scenario_run.status,
                  "step_index": (
                      scenario_run.current_step_run.index
                      if scenario_run.current_step_run is not None
                      else None
                  ),
              }
          )


      @hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_runtest_call(item):
          if item.get_closest_marker("pytest_cuke_scenario") is None:
              yield
              return

          run_context = item._request.getfixturevalue("run_context")
          _snapshot(run_context, "setup")
          yield

          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          _snapshot(run_context, "finished")
          snapshots = _phase_snapshots[scenario_run.nodeid]
          with Path("runtime-sequence-observations.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(
                  json.dumps(
                      {
                          "nodeid": scenario_run.nodeid,
                          "scenario_name": scenario_run.scenario.name,
                          "scenario_identity": id(scenario_run),
                          "run_id": scenario_run.run_id,
                          "attempt_id": scenario_run.attempt_id,
                          "test_case_id": scenario_run.test_case_id,
                          "test_case_started_id": scenario_run.test_case_started_id,
                          "binding_identity": id(scenario_run.feature_binding),
                          "feature_uri": scenario_run.feature_binding.uri,
                          "row_value": scenario_run.context.user_data["row"],
                          "status": scenario_run.status,
                          "steps": [
                              {"id": step_run.id, "status": step_run.status, "result": step_run.result}
                              for step_run in scenario_run.steps
                          ],
                          "snapshots": snapshots,
                      },
                      sort_keys=True,
                  )
                  + "\n"
              )


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          _snapshot(request.getfixturevalue("run_context"), "pytest_cuke_before_scenario")


      @hookimpl
      def pytest_cuke_before_step(request, run, step_func):
          _snapshot(request.getfixturevalue("run_context"), "pytest_cuke_before_step")


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          run_context = request.getfixturevalue("run_context")
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          assert run_context.active_scenario_run is scenario_run
          assert run_context.active_feature_binding is scenario_run.feature_binding
          assert run_context.get_scenario_run(request.node.nodeid) is scenario_run
          assert scenario_run.nodeid == request.node.nodeid
          assert run_context.stage == "finished"
          assert run_context.status == "passed"
          assert run_context.hook_phase == "pytest_cuke_after_scenario"
          assert scenario_run.status == "passed"
          previous_step_hook = _phase_snapshots[scenario_run.nodeid][-1]
          assert run_context.transition_index > previous_step_hook["transition_index"]
          _snapshot(run_context, "pytest_cuke_after_scenario")


      @given(parsers.parse('the isolated runtime row is "{label}"'))
      def isolated_runtime_row_is(label, run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          assert scenario_run.context.user_data == {}
          assert scenario_run.current_step_run.index == 0
          assert scenario_run.current_step_run.previous_step_run is None
          scenario_run.context.user_data["row"] = label
          return label


      @when(parsers.parse('I inspect the prior runtime step for "{label}"'))
      def inspect_prior_runtime_step(label, run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          assert scenario_run.context.user_data == {"row": label}
          current = scenario_run.current_step_run
          assert current is not None and current.index == 1
          assert current.previous_step_run is scenario_run.steps[0]
          assert current.previous_step_run.result == label
          return f"{label}:verified"


      @then(parsers.parse('the runtime row "{label}" is complete'))
      def runtime_row_is_complete(label, run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          assert scenario_run.context.user_data == {"row": label}
          current = scenario_run.current_step_run
          assert current is not None and current.index == 2
          assert current.previous_step_run is scenario_run.steps[1]
          assert current.previous_step_run.result == f"{label}:verified"
      """
    And consumer file "features/runtime-sequence.feature" contains:
      """gherkin
      Feature: Sequential runtime contexts
        Scenario: The first ordinary scenario has clean step state
          Given the isolated runtime row is "ordinary-one"
          When I inspect the prior runtime step for "ordinary-one"
          Then the runtime row "ordinary-one" is complete

        Scenario: The second ordinary scenario starts with clean step state
          Given the isolated runtime row is "ordinary-two"
          When I inspect the prior runtime step for "ordinary-two"
          Then the runtime row "ordinary-two" is complete

        Scenario Outline: Each outline row starts with clean step state for <label>
          Given the isolated runtime row is "<label>"
          When I inspect the prior runtime step for "<label>"
          Then the runtime row "<label>" is complete

          Examples:
            | label     |
            | outline-a |
            | outline-b |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=runtime-sequence.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 4 passed scenarios
    And consumer runtime artifact "runtime-sequence-observations.jsonl" should show isolated rows and monotonic hook phases

  Scenario: A teardown failure does not leak into following BDD and plain pytest items
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import fixture, hookimpl
      from pytest_cuke import given


      _run_contexts = {}


      def _append_observation(value):
          with Path("runtime-cleanup-observations.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(value, sort_keys=True) + "\n")


      @fixture
      def teardown_failure_sentinel():
          yield
          raise RuntimeError("runtime teardown failure sentinel")


      @given("the BDD item requests a teardown failure")
      def bdd_item_requests_teardown_failure(teardown_failure_sentinel, run_context):
          assert run_context.status == "running"


      @given("a fresh BDD item follows the teardown failure")
      def fresh_bdd_item_follows_teardown_failure(run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          assert run_context.last_error is None
          assert scenario_run.context.user_data == {}
          assert scenario_run.current_step_run.index == 0
          assert scenario_run.current_step_run.previous_step_run is None
          scenario_run.context.user_data["fresh"] = True


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          _run_contexts[request.node.nodeid] = request.getfixturevalue("run_context")


      def pytest_collection_modifyitems(items):
          def order(item):
              params = getattr(getattr(item, "callspec", None), "params", {})
              scenario = params.get("scenario")
              name = getattr(scenario, "name", "")
              if item.get_closest_marker("pytest_cuke_scenario") is None:
                  return (2, item.nodeid)
              if name == "Teardown failure happens before the next scenario":
                  return (0, item.nodeid)
              return (1, item.nodeid)

          items.sort(key=order)


      @hookimpl(hookwrapper=True)
      def pytest_runtest_makereport(item, call):
          outcome = yield
          if item.get_closest_marker("pytest_cuke_scenario") is None:
              return

          run_context = _run_contexts.get(item.nodeid)
          if run_context is None:
              return
          scenario_run = run_context.get_scenario_run(item.nodeid)
          if scenario_run is None:
              return
          params = getattr(getattr(item, "callspec", None), "params", {})
          scenario = params.get("scenario")
          snapshot = {
              "scenario_name": getattr(scenario, "name", ""),
              "phase": call.when,
              "run_id": scenario_run.run_id,
              "scenario_identity": id(scenario_run),
              "attempt_id": scenario_run.attempt_id,
              "test_case_started_id": scenario_run.test_case_started_id,
              "status": scenario_run.status,
              "active_scenario": run_context.active_scenario_run is not None,
              "last_error": str(run_context.last_error) if run_context.last_error else None,
          }
          _append_observation(snapshot)
      """
    And consumer file "test_plain_runtime.py" contains:
      """python
      import json
      from pathlib import Path


      def test_plain_pytest_after_bdd_cleanup(run_context):
          assert run_context.active_feature_binding is None
          assert run_context.active_scenario_run is None
          assert run_context.status == "inactive"
          assert run_context.last_error is None
          Path("plain-after-bdd-observation.json").write_text(
              json.dumps(
                  {
                      "active_feature_binding": run_context.active_feature_binding is not None,
                      "active_scenario_run": run_context.active_scenario_run is not None,
                      "status": run_context.status,
                      "last_error": str(run_context.last_error) if run_context.last_error else None,
                      "scenario_count": len(run_context.scenario_runs_by_nodeid),
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/runtime-recovery.feature" contains:
      """gherkin
      Feature: Runtime recovery after teardown
        Scenario: Teardown failure happens before the next scenario
          Given the BDD item requests a teardown failure

        Scenario: A fresh scenario follows a teardown failure
          Given a fresh BDD item follows the teardown failure
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 1
    And consumer runtime artifact "runtime-cleanup-observations.jsonl" should show failed teardown then clean BDD state
    And consumer runtime snapshot "plain-after-bdd-observation.json" should show clean plain pytest state after BDD teardown

  Scenario: A nonterminal tolerant failure and teardown failure remain visible in reporting
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import pytest

      from pytest_cuke import then, when
      from pytest_cuke.steps import tolerant


      @pytest.fixture
      def fail_during_teardown():
          yield
          raise RuntimeError("late teardown failure sentinel")


      @tolerant
      @when("the nonterminal tolerant step fails")
      def nonterminal_tolerant_step_fails():
          raise AssertionError("nonterminal tolerant assertion sentinel")


      @then("a later step passes")
      def later_step_passes(fail_during_teardown):
          assert fail_during_teardown is None
      """
    And consumer file "features/tolerant-teardown-runtime.feature" contains:
      """gherkin
      Feature: Reporting a tolerant step failure followed by teardown failure
        Scenario: The tolerant failure and teardown error are both reported
          When the nonterminal tolerant step fails
          Then a later step passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=tolerant-teardown-runtime.ndjson --cuke-json=tolerant-teardown-runtime.json -q"
    Then pytest should exit with code 1
    And consumer runtime artifacts "tolerant-teardown-runtime.ndjson" and "tolerant-teardown-runtime.json" should retain both step and teardown errors

  Scenario: Assertion failure, undefined lookup, and skip finish with distinct runtime outcomes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      import pytest
      from pytest import hookimpl
      from pytest_cuke import given, then


      _terminal_run_contexts = {}


      @given("a runtime step raises an assertion")
      def runtime_step_raises_assertion():
          raise AssertionError("runtime assertion sentinel")


      @then("a runtime step requests a skip")
      def runtime_step_requests_skip():
          pytest.skip("runtime skip sentinel")


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          _terminal_run_contexts[request.node.nodeid] = request.getfixturevalue("run_context")


      @hookimpl(hookwrapper=True)
      def pytest_runtest_makereport(item, call):
          yield
          if call.when != "teardown" or item.get_closest_marker("pytest_cuke_scenario") is None:
              return

          run_context = _terminal_run_contexts.get(item.nodeid)
          if run_context is None:
              return
          scenario_run = run_context.get_scenario_run(item.nodeid)
          assert scenario_run is not None
          step_run = scenario_run.steps[-1] if scenario_run.steps else None
          observation = {
              "scenario_name": scenario_run.scenario.name,
              "run_id": scenario_run.run_id,
              "attempt_id": scenario_run.attempt_id,
              "test_case_id": scenario_run.test_case_id,
              "test_case_started_id": scenario_run.test_case_started_id,
              "scenario_status": scenario_run.status,
              "exception_type": type(scenario_run.exception).__name__ if scenario_run.exception else None,
              "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
              "step_status": step_run.status if step_run is not None else None,
              "root_status": run_context.status,
              "root_stage": run_context.stage,
              "root_hook_phase": run_context.hook_phase,
              "last_error_type": type(run_context.last_error).__name__ if run_context.last_error else None,
              "active_feature_binding": run_context.active_feature_binding is not None,
              "active_scenario_run": run_context.active_scenario_run is not None,
          }
          with Path("runtime-terminal-outcomes.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(observation, sort_keys=True) + "\n")
      """
    And consumer file "features/runtime-terminal-outcomes.feature" contains:
      """gherkin
      Feature: Distinct runtime terminal outcomes
        Scenario: Assertion failure is retained after teardown cleanup
          Given a runtime step raises an assertion

        Scenario: Undefined lookup is retained after teardown cleanup
          When an undefined runtime step is requested

        Scenario: Skip is retained after teardown cleanup
          Then a runtime step requests a skip
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=runtime-terminal-outcomes.ndjson -q"
    Then pytest should exit with code 1
    And consumer runtime artifacts "runtime-terminal-outcomes.jsonl" and "runtime-terminal-outcomes.ndjson" should retain distinct terminal outcomes after cleanup

  Scenario: Rule Background steps retain runtime links in Messages and JSON reports
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given, parsers, then, when


      def _assert_domain_node_is_frozen(value):
          marker = "_pytest_cuke_runtime_marker"
          assert not hasattr(value, marker)
          try:
              setattr(value, marker, True)
          except (AttributeError, TypeError):
              pass
          else:
              raise AssertionError(f"runtime metadata was attached to frozen {type(value).__name__}")
          assert not hasattr(value, marker)


      @given(parsers.parse("the runtime total starts at {total:d}"), target_fixture="runtime_total")
      def runtime_total_starts_at(total):
          return total


      @given(parsers.parse("I add {amount:d} to the runtime total"), target_fixture="runtime_total")
      def add_to_runtime_total(runtime_total, amount):
          return runtime_total + amount


      @when(parsers.parse("I add {amount:d} more to the runtime total"), target_fixture="runtime_total")
      def add_more_to_runtime_total(runtime_total, amount, run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          scenario_run.context.user_data["outline_amount"] = amount
          return runtime_total + amount


      @then(parsers.parse("the runtime total is {expected:d}"))
      def runtime_total_is(runtime_total, expected):
          assert runtime_total == expected


      @then("the runtime DocString preserves outline parameters")
      def runtime_docstring_preserves_outline_parameters(step, runtime_total, run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          amount = scenario_run.context.user_data["outline_amount"]
          assert step.doc_string is not None
          assert step.doc_string.media_type == "application/json"
          assert step.doc_string.content.strip() == f"amount={amount};expected={runtime_total}"


      @then("the runtime DataTable preserves outline parameters")
      def runtime_datatable_preserves_outline_parameters(step, runtime_total, run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          amount = scenario_run.context.user_data["outline_amount"]
          assert step.data_table is not None
          assert step.data_table.as_dicts() == [
              {"field": "amount", "value": str(amount)},
              {"field": "expected", "value": str(runtime_total)},
          ]


      @hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_runtest_call(item):
          if item.get_closest_marker("pytest_cuke_scenario") is None:
              yield
              return

          run_context = item._request.getfixturevalue("run_context")
          yield

          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          binding = scenario_run.feature_binding
          assert binding is not None
          feature = binding.feature
          source_scenario_id = scenario_run.scenario.source_ast_node_ids[0]
          source_scenario = next(
              candidate for candidate in feature.all_scenarios if candidate.id == source_scenario_id
          )
          assert binding.resolve_scenario(scenario_run.scenario.source_ast_node_ids) is scenario_run.scenario
          assert binding.document is not None and binding.document.feature is feature
          source_lines = binding.source.splitlines()
          domain_nodes = [feature, binding.document, source_scenario, scenario_run.scenario]
          domain_nodes.extend(feature.all_scenarios)
          domain_nodes.extend(feature.rules)
          for background in (feature.background, *(rule.background for rule in feature.rules)):
              if background is not None:
                  domain_nodes.append(background)
                  domain_nodes.extend(background.steps)
          for scenario in feature.all_scenarios:
              domain_nodes.extend(scenario.steps)
              for examples in scenario.examples:
                  domain_nodes.extend((examples, examples.header))
                  domain_nodes.extend(examples.rows)
                  domain_nodes.extend(cell for row in examples.rows for cell in row.cells)

          runtime_steps = []
          for step_run in scenario_run.steps:
              runtime_step = step_run.step
              source_step = binding.resolve_step(runtime_step)
              assert source_step is not None
              assert source_step.id == runtime_step.id
              assert source_step.line == runtime_step.line
              assert source_lines[source_step.line - 1].strip().endswith(source_step.name)
              domain_nodes.extend((source_step, runtime_step))

              doc_string = None
              if runtime_step.doc_string is not None:
                  assert source_step.doc_string is not None
                  doc_string = {
                      "content": runtime_step.doc_string.content,
                      "source_content": source_step.doc_string.content,
                      "media_type": runtime_step.doc_string.media_type,
                      "source_media_type": source_step.doc_string.media_type,
                      "line": runtime_step.doc_string.line,
                      "source_line": source_step.doc_string.line,
                  }
                  assert runtime_step.doc_string.line == source_step.doc_string.line
                  assert source_lines[source_step.doc_string.line - 1].strip().startswith("```")
                  domain_nodes.extend((runtime_step.doc_string, source_step.doc_string))

              data_table = None
              if runtime_step.data_table is not None:
                  assert source_step.data_table is not None
                  data_table = {
                      "rows": [
                          {
                              "line": row.line,
                              "cells": [{"value": cell.value, "line": cell.line, "id": cell.id} for cell in row.cells],
                          }
                          for row in runtime_step.data_table.rows
                      ],
                      "source_rows": [
                          {
                              "line": row.line,
                              "cells": [{"value": cell.value, "line": cell.line, "id": cell.id} for cell in row.cells],
                          }
                          for row in source_step.data_table.rows
                      ],
                      "line": runtime_step.data_table.line,
                      "source_line": source_step.data_table.line,
                  }
                  assert runtime_step.data_table.line == source_step.data_table.line
                  assert source_lines[source_step.data_table.line - 1].strip().startswith("|")
                  domain_nodes.extend((runtime_step.data_table, source_step.data_table))
                  domain_nodes.extend(row for row in runtime_step.data_table.rows)
                  domain_nodes.extend(cell for row in runtime_step.data_table.rows for cell in row.cells)
                  domain_nodes.extend(row for row in source_step.data_table.rows)
                  domain_nodes.extend(cell for row in source_step.data_table.rows for cell in row.cells)

              runtime_steps.append(
                  {
                      "id": runtime_step.id,
                      "test_step_id": step_run.test_step_id,
                      "text": runtime_step.name,
                      "source_text": source_step.name,
                      "source_step_id": source_step.id,
                      "line": runtime_step.line,
                      "source_line": source_step.line,
                      "status": step_run.status,
                      "doc_string": doc_string,
                      "data_table": data_table,
                  }
              )

          for node in domain_nodes:
              if node is not None:
                  _assert_domain_node_is_frozen(node)

          observation = {
              "nodeid": scenario_run.nodeid,
              "scenario_name": scenario_run.scenario.name,
              "feature_uri": scenario_run.feature_binding.uri,
              "binding_identity": id(binding),
              "source_scenario_id": source_scenario.id,
              "source_scenario_name": source_scenario.name,
              "source_ast_node_ids": list(scenario_run.scenario.source_ast_node_ids),
              "test_case_id": scenario_run.test_case_id,
              "test_case_started_id": scenario_run.test_case_started_id,
              "steps": runtime_steps,
          }
          with Path("rule-runtime-observations.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(observation, sort_keys=True) + "\n")
      """
    And consumer file "features/rule-runtime.feature" contains:
      """gherkin
      Feature: Runtime links for Rule Background steps
        Background:
          Given the runtime total starts at 1

        Rule: Rule Background execution is reported
          Background:
            Given I add 10 to the runtime total

          Scenario Outline: The runtime total includes the Rule Background for <amount>
            When I add <amount> more to the runtime total
            Then the runtime total is <expected>
            And the runtime DocString preserves outline parameters
              ```application/json
              amount=<amount>;expected=<expected>
              ```
            And the runtime DataTable preserves outline parameters
              | field    | value      |
              | amount   | <amount>   |
              | expected | <expected> |

            Examples:
              | amount | expected |
              | 2      | 13       |
              | 6      | 17       |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=rule-runtime.ndjson --cuke-json=rule-runtime.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer runtime artifacts "rule-runtime-observations.jsonl", "rule-runtime.ndjson" and "rule-runtime.json" should agree on Rule Background step links

  Scenario: Repeated pytest sessions in one process receive separate runtime roots
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given


      @given("the repeated session scenario runs")
      def repeated_session_scenario_runs():
          pass


      @hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_runtest_call(item):
          if item.get_closest_marker("pytest_cuke_scenario") is None:
              yield
              return

          run_context = item._request.getfixturevalue("run_context")
          yield

          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          with Path("repeat-runtime-observations.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(
                  json.dumps(
                      {
                          "run_id": scenario_run.run_id,
                          "attempt_id": scenario_run.attempt_id,
                          "test_case_id": scenario_run.test_case_id,
                          "test_case_started_id": scenario_run.test_case_started_id,
                      },
                      sort_keys=True,
                  )
                  + "\n"
              )
      """
    And consumer file "features/repeat-runtime.feature" contains:
      """gherkin
      Feature: Repeated session runtime roots
        Scenario: One scenario runs in each pytest session
          Given the repeated session scenario runs
      """
    When I run installed pytest twice in one process with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=first-session.ndjson -q" and then "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=second-session.ndjson -q"
    Then consumer repeated pytest sessions should exit with codes "0,0"
    And consumer runtime artifacts "repeat-runtime-observations.jsonl", "first-session.ndjson" and "second-session.ndjson" should have independent run and scenario IDs

  Scenario: Xdist workers keep separate runtime roots for installed feature files
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import json
      import os
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given, parsers


      @given(parsers.parse("the xdist runtime source is {source}"))
      def xdist_runtime_source_is(source):
          assert source in {"north", "south"}


      @hookimpl(hookwrapper=True, trylast=True)
      def pytest_cuke_before_scenario(request, run):
          yield
          run_context = request.getfixturevalue("run_context")
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          worker = os.environ.get("PYTEST_XDIST_WORKER", "master")
          with Path(f"runtime-{worker}.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(
                  json.dumps(
                      {
                          "worker": worker,
                          "run_id": run_context.run_id,
                          "nodeid": scenario_run.nodeid,
                          "attempt_id": scenario_run.attempt_id,
                          "test_case_id": scenario_run.test_case_id,
                          "test_case_started_id": scenario_run.test_case_started_id,
                      },
                      sort_keys=True,
                  )
                  + "\n"
              )
      """
    And consumer file "features/north-runtime.feature" contains:
      """gherkin
      Feature: North xdist runtime source
        Scenario: North has its own worker root
          Given the xdist runtime source is north
      """
    And consumer file "features/south-runtime.feature" contains:
      """gherkin
      Feature: South xdist runtime source
        Scenario: South has its own worker root
          Given the xdist runtime source is south
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=xdist-runtime.ndjson -n2 --dist=loadfile -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer xdist runtime artifacts should show separate run roots in "xdist-runtime.ndjson"

  Scenario: A plain pytest report stays inactive after an autoloaded BDD scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import fixture, hookimpl
      from pytest_cuke import given


      _bdd_run_context = None
      _bdd_nodeid = None


      def _append_observation(value):
          with Path("inactive-reporting-observations.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(value, sort_keys=True) + "\n")


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _bdd_run_context, _bdd_nodeid
          _bdd_run_context = request.getfixturevalue("run_context")
          _bdd_nodeid = request.node.nodeid


      @given("the BDD reporting scenario is active")
      def bdd_reporting_scenario_is_active(run_context):
          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          assert run_context.active_feature_binding is scenario_run.feature_binding
          assert scenario_run.test_case_started_id
          _append_observation(
              {
                  "kind": "bdd",
                  "nodeid": scenario_run.nodeid,
                  "scenario_name": scenario_run.scenario.name,
                  "run_context_identity": id(run_context),
                  "run_id": run_context.run_id,
                  "run_status": run_context.status,
                  "scenario_identity": id(scenario_run),
                  "test_case_id": scenario_run.test_case_id,
                  "test_case_started_id": scenario_run.test_case_started_id,
                  "test_step_ids": list(scenario_run.test_step_ids),
              }
          )


      @fixture
      def prior_bdd_run():
          assert _bdd_run_context is not None
          return _bdd_run_context


      def pytest_collection_modifyitems(items):
          items.sort(key=lambda item: item.get_closest_marker("pytest_cuke_scenario") is None)
      """
    And consumer file "features/inactive-reporting.feature" contains:
      """gherkin
      Feature: Reporting outside an active BDD scenario
        Scenario: The BDD reporting scenario is the only reported scenario
          Given the BDD reporting scenario is active
      """
    And consumer file "test_plain_reporting.py" contains:
      """python
      import json
      from pathlib import Path


      def test_plain_item_uses_inactive_session_runtime(run_context, prior_bdd_run):
          assert run_context is prior_bdd_run
          assert run_context.active_feature_binding is None
          assert run_context.active_scenario_run is None
          assert run_context.status == "inactive"
          assert run_context.stage == "inactive"
          assert run_context.hook_phase == "inactive"
          assert run_context.get_scenario_run(next(iter(run_context.scenario_runs_by_nodeid))) is not None
          Path("plain-reporting-observation.json").write_text(
              json.dumps(
                  {
                      "run_context_identity": id(run_context),
                      "run_id": run_context.run_id,
                      "run_status": run_context.status,
                      "run_stage": run_context.stage,
                      "run_hook_phase": run_context.hook_phase,
                      "active_feature_binding": run_context.active_feature_binding is not None,
                      "active_scenario_run": run_context.active_scenario_run is not None,
                      "scenario_count": len(run_context.scenario_runs_by_nodeid),
                      "prior_nodeid": next(iter(run_context.scenario_runs_by_nodeid)),
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=inactive-reporting.ndjson --cuke-json=inactive-reporting.json -q"
    Then pytest should exit with code 0
    And pytest output should include "2 passed"
    And consumer runtime artifacts "inactive-reporting-observations.jsonl", "plain-reporting-observation.json", "inactive-reporting.ndjson" and "inactive-reporting.json" should exclude plain pytest from BDD reporting

  Scenario: Distinct feature sources keep overlapping scenario and step identities separate
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given


      @given("the same source step name executes")
      def the_same_source_step_name_executes():
          pass


      @hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_runtest_call(item):
          if item.get_closest_marker("pytest_cuke_scenario") is None:
              yield
              return

          run_context = item._request.getfixturevalue("run_context")
          yield

          scenario_run = run_context.active_scenario_run
          assert scenario_run is not None
          binding = scenario_run.feature_binding
          source_scenario = next(
              candidate
              for candidate in binding.feature.all_scenarios
              if candidate.id == scenario_run.scenario.id and candidate.name == scenario_run.scenario.name
          )
          source_scenario_id = source_scenario.id
          assert source_scenario_id
          runtime_steps = []
          for step_run in scenario_run.steps:
              source_step = binding.resolve_step(step_run.step)
              assert source_step is not None
              runtime_steps.append(
                  {
                      "name": step_run.step.name,
                      "source_step_id": source_step.id,
                      "source_line": source_step.line,
                      "test_step_id": step_run.test_step_id,
                      "status": step_run.status,
                  }
              )

          observation = {
              "scenario_name": scenario_run.scenario.name,
              "feature_uri": binding.uri,
              "binding_identity": id(binding),
              "registered_binding_identity": id(run_context.feature_bindings_by_uri[binding.uri]),
              "source_scenario_id": source_scenario_id,
              "resolved_source_scenario_id": source_scenario.id,
              "run_id": scenario_run.run_id,
              "test_case_id": scenario_run.test_case_id,
              "test_case_started_id": scenario_run.test_case_started_id,
              "steps": runtime_steps,
          }
          with Path("source-identity-observations.jsonl").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(observation, sort_keys=True) + "\n")
      """
    And consumer file "features/source-one.feature" contains:
      """gherkin
      Feature: Overlapping runtime source identities
        Scenario: The same scenario name executes
          Given the same source step name executes
      """
    And consumer file "features/source-two.feature" contains:
      """gherkin
      Feature: Overlapping runtime source identities
        Scenario: The same scenario name executes
          Given the same source step name executes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=source-identity.ndjson --cuke-json=source-identity.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer runtime artifacts "source-identity-observations.jsonl", "source-identity.ndjson" and "source-identity.json" should keep source bindings and report identities separate

  Scenario: An interrupted scenario remains distinct from a failed scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import hookimpl
      from pytest_cuke import given


      _run_context = None
      _scenario_nodeid = None


      def _write_snapshot(path, value):
          Path(path).write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @given("the runtime step interrupts pytest")
      def runtime_step_interrupts_pytest():
          raise KeyboardInterrupt("runtime interrupt sentinel")


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = _run_context.active_scenario_run
          _write_snapshot(
              "interrupt-after-scenario.json",
              {
                  "scenario_name": run.scenario.name,
                  "scenario_status": scenario_run.status if scenario_run is not None else None,
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
                  "active_scenario_run": _run_context.active_scenario_run is not None,
                  "test_case_id": scenario_run.test_case_id if scenario_run is not None else None,
                  "test_case_started_id": scenario_run.test_case_started_id if scenario_run is not None else None,
                  "test_step_ids": list(scenario_run.test_step_ids) if scenario_run is not None else [],
              },
          )


      @hookimpl(trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          if _run_context is None or _scenario_nodeid is None:
              return

          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          _write_snapshot(
              "interrupt-session-history.json",
              {
                  "scenario_history_found": scenario_run is not None,
                  "scenario_status": scenario_run.status if scenario_run is not None else None,
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
                  "active_feature_binding": _run_context.active_feature_binding is not None,
                  "active_scenario_run": _run_context.active_scenario_run is not None,
                  "active_step": scenario_run.current_step_run is not None if scenario_run is not None else None,
                  "exit_status": int(exitstatus),
              },
          )
      """
    And consumer file "features/interrupted-runtime.feature" contains:
      """gherkin
      Feature: Interrupted runtime outcomes
        Scenario: KeyboardInterrupt leaves an interrupted runtime outcome
          Given the runtime step interrupts pytest
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=interrupt-messages.ndjson --cuke-json=interrupt-report.json -q"
    Then the interrupted consumer should exit with code 2, retain runtime artifacts "interrupt-after-scenario.json" and "interrupt-session-history.json", and report an UNKNOWN Messages step in "interrupt-messages.ndjson" and an UNKNOWN JSON result in "interrupt-report.json"

  Scenario: A teardown KeyboardInterrupt is retained by runtime and reporting
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import fixture, hookimpl
      from pytest_cuke import given, then, when


      _run_context = None
      _scenario_nodeid = None


      def _write_runtime_snapshot(path, scenario_run, run_context, **extra):
          Path(path).write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "exception_type": type(scenario_run.exception).__name__ if scenario_run.exception else None,
                      "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
                      "test_case_id": scenario_run.test_case_id,
                      "test_case_started_id": scenario_run.test_case_started_id,
                      "test_step_ids": list(scenario_run.test_step_ids),
                      "step_statuses": [step_run.status for step_run in scenario_run.steps],
                      "active_feature_binding": run_context.active_feature_binding is not None,
                      "active_scenario_run": run_context.active_scenario_run is not None,
                      **extra,
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )


      @fixture
      def interrupting_teardown():
          yield
          raise KeyboardInterrupt("teardown interrupt sentinel")


      @given("the scenario arms a KeyboardInterrupt during fixture teardown")
      def scenario_arms_teardown_interrupt(interrupting_teardown):
          assert interrupting_teardown is None


      @when("the first runtime action completes")
      def first_runtime_action_completes():
          return "first action complete"


      @then("the terminal runtime action completes before pytest teardown")
      def terminal_runtime_action_completes():
          return "terminal action complete"


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = _run_context.active_scenario_run
          assert scenario_run is not None
          _write_runtime_snapshot(
              "teardown-after-scenario.json",
              scenario_run,
              _run_context,
              scenario_name=run.scenario.name,
          )


      @hookimpl(trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          if _run_context is None or _scenario_nodeid is None:
              return
          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          assert scenario_run is not None
          _write_runtime_snapshot(
              "teardown-runtime.json",
              scenario_run,
              _run_context,
              runtime_status=_run_context.status,
              runtime_stage=_run_context.stage,
              exit_status=int(exitstatus),
          )
      """
    And consumer file "features/teardown-interrupted-runtime.feature" contains:
      """gherkin
      Feature: Runtime state after teardown interruption
        Scenario: Fixture teardown interrupts a completed multi-step scenario
          Given the scenario arms a KeyboardInterrupt during fixture teardown
          When the first runtime action completes
          Then the terminal runtime action completes before pytest teardown
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=teardown-interrupt-messages.ndjson --cuke-json=teardown-interrupt-report.json -q"
    Then pytest should exit with code 2
    And consumer runtime artifacts "teardown-after-scenario.json", "teardown-runtime.json", "teardown-interrupt-messages.ndjson" and "teardown-interrupt-report.json" should retain the teardown interruption

  Scenario: A teardown KeyboardInterrupt overrides a skipped terminal step
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      import pytest
      from pytest import fixture, hookimpl
      from pytest_cuke import given, when, then


      @fixture
      def interrupting_teardown_after_skip():
          yield
          raise KeyboardInterrupt("teardown after skipped-step sentinel")


      @given("the scenario arms teardown interruption after its terminal step")
      def scenario_arms_teardown_interrupt_after_skip(interrupting_teardown_after_skip):
          assert interrupting_teardown_after_skip is None


      @when("the preliminary scenario action completes")
      def preliminary_scenario_action_completes():
          return "preliminary action complete"


      @then("the terminal scenario step is skipped")
      def terminal_scenario_step_is_skipped():
          pytest.skip("terminal scenario step skip sentinel")


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = request.getfixturevalue("run_context").active_scenario_run
          assert scenario_run is not None
          Path("terminal-skip-before-teardown.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "terminal_step_status": scenario_run.steps[-1].status,
                      "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/terminal-skip-interrupted-runtime.feature" contains:
      """gherkin
      Feature: Runtime reporting after a skipped step and teardown interruption
        Scenario: Fixture teardown interrupts after its terminal step skips
          Given the scenario arms teardown interruption after its terminal step
          When the preliminary scenario action completes
          Then the terminal scenario step is skipped
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=terminal-skip-interrupt-messages.ndjson --cuke-json=terminal-skip-interrupt-report.json -q"
    Then pytest should exit with code 2
    And consumer artifacts "terminal-skip-before-teardown.json", "terminal-skip-interrupt-messages.ndjson" and "terminal-skip-interrupt-report.json" should report the teardown interruption over the skipped terminal step

  Scenario: A teardown KeyboardInterrupt preserves a terminal assertion failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import fixture, hookimpl
      from pytest_cuke import given, when, then


      _run_context = None
      _scenario_nodeid = None


      def _write_snapshot(path, scenario_run, run_context, **extra):
          Path(path).write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "exception_type": type(scenario_run.exception).__name__ if scenario_run.exception else None,
                      "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
                      "test_case_id": scenario_run.test_case_id,
                      "test_case_started_id": scenario_run.test_case_started_id,
                      "test_step_ids": list(scenario_run.test_step_ids),
                      "step_statuses": [step_run.status for step_run in scenario_run.steps],
                      "active_feature_binding": run_context.active_feature_binding is not None,
                      "active_scenario_run": run_context.active_scenario_run is not None,
                      **extra,
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )


      @fixture
      def interrupting_teardown_after_assertion():
          yield
          raise KeyboardInterrupt("teardown after assertion sentinel")


      @given("the scenario arms teardown interruption after its terminal assertion")
      def scenario_arms_teardown_interrupt_after_assertion(interrupting_teardown_after_assertion):
          assert interrupting_teardown_after_assertion is None


      @when("the preliminary assertion scenario action completes")
      def preliminary_assertion_scenario_action_completes():
          return "preliminary action complete"


      @then("the terminal runtime assertion fails with its sentinel")
      def terminal_runtime_assertion_fails_with_sentinel():
          raise AssertionError("terminal assertion sentinel")


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = _run_context.active_scenario_run
          assert scenario_run is not None
          terminal_step = scenario_run.steps[-1]
          Path("assertion-before-teardown.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "terminal_step_status": terminal_step.status,
                      "terminal_step_exception_type": type(terminal_step.exception).__name__
                      if terminal_step.exception
                      else None,
                      "terminal_step_exception_message": str(terminal_step.exception)
                      if terminal_step.exception
                      else None,
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )


      @hookimpl(trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          if _run_context is None or _scenario_nodeid is None:
              return
          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          assert scenario_run is not None
          _write_snapshot(
              "assertion-teardown-runtime.json",
              scenario_run,
              _run_context,
              runtime_status=_run_context.status,
              runtime_stage=_run_context.stage,
              exit_status=int(exitstatus),
          )
      """
    And consumer file "features/assertion-teardown-interrupted-runtime.feature" contains:
      """gherkin
      Feature: Runtime reporting after assertion failure and teardown interruption
        Scenario: Fixture teardown interrupts after a terminal assertion fails
          Given the scenario arms teardown interruption after its terminal assertion
          When the preliminary assertion scenario action completes
          Then the terminal runtime assertion fails with its sentinel
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=assertion-teardown-messages.ndjson --cuke-json=assertion-teardown-report.json -q"
    Then pytest should exit with code 2
    And consumer runtime artifacts "assertion-before-teardown.json", "assertion-teardown-runtime.json", "assertion-teardown-messages.ndjson" and "assertion-teardown-report.json" should retain both assertion reporting and the teardown error

  Scenario: A teardown KeyboardInterrupt preserves a middle skipped step
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      import pytest
      from pytest import fixture, hookimpl
      from pytest_cuke import given, when, then


      _run_context = None
      _scenario_nodeid = None


      @fixture
      def interrupting_teardown_after_middle_skip():
          yield
          raise KeyboardInterrupt("teardown after middle skip sentinel")


      @given("the scenario arms teardown interruption after its middle step")
      def scenario_arms_teardown_interrupt_after_middle_skip(interrupting_teardown_after_middle_skip):
          assert interrupting_teardown_after_middle_skip is None


      @when("the first scenario action completes")
      def first_scenario_action_completes():
          return "first action complete"


      @when("the middle scenario step is skipped")
      def middle_scenario_step_is_skipped():
          pytest.skip("middle scenario step skip sentinel")


      @then("the final scenario step remains unstarted")
      def final_scenario_step_remains_unstarted():
          return "unreachable final action"


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = _run_context.active_scenario_run
          assert scenario_run is not None
          Path("middle-skip-before-teardown.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "scenario_step_count": len(run.scenario.steps),
                      "executed_step_names": [step_run.step.text for step_run in scenario_run.steps],
                      "executed_step_statuses": [step_run.status for step_run in scenario_run.steps],
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )


      @hookimpl(trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          if _run_context is None or _scenario_nodeid is None:
              return
          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          assert scenario_run is not None
          Path("middle-skip-teardown-runtime.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "exception_type": type(scenario_run.exception).__name__ if scenario_run.exception else None,
                      "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
                      "runtime_status": _run_context.status,
                      "active_feature_binding": _run_context.active_feature_binding is not None,
                      "active_scenario_run": _run_context.active_scenario_run is not None,
                      "exit_status": int(exitstatus),
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/middle-skip-interrupted-runtime.feature" contains:
      """gherkin
      Feature: Runtime reporting after a middle step skip and teardown interruption
        Scenario: Fixture teardown interrupts after the middle scenario step skips
          Given the scenario arms teardown interruption after its middle step
          When the first scenario action completes
          When the middle scenario step is skipped
          Then the final scenario step remains unstarted
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=middle-skip-interrupt-messages.ndjson --cuke-json=middle-skip-interrupt-report.json -q"
    Then pytest should exit with code 2
    And consumer runtime artifacts "middle-skip-before-teardown.json", "middle-skip-teardown-runtime.json", "middle-skip-interrupt-messages.ndjson" and "middle-skip-interrupt-report.json" should preserve skipped and interrupted step outcomes

  Scenario: A teardown KeyboardInterrupt marks only the passed terminal step unknown
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      import pytest
      from pytest import hookimpl
      from pytest_cuke import then, when
      from pytest_cuke.steps import tolerant


      _run_context = None
      _scenario_nodeid = None


      @pytest.fixture(autouse=True)
      def interrupting_teardown_after_tolerant_step():
          yield
          raise KeyboardInterrupt("teardown after tolerant step sentinel")


      @tolerant
      @when("the tolerant first step raises an AssertionError and continues")
      def tolerant_first_step_records_failure():
          raise AssertionError("tolerant first-step assertion sentinel")


      @then("the terminal scenario step completes successfully")
      def terminal_scenario_step_completes_successfully():
          return "terminal step passed"


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = _run_context.active_scenario_run
          assert scenario_run is not None
          Path("tolerant-before-teardown.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "step_names": [step_run.step.text for step_run in scenario_run.steps],
                      "step_statuses": [step_run.status for step_run in scenario_run.steps],
                      "step_exception_messages": [
                          str(step_run.exception) if step_run.exception is not None else None
                          for step_run in scenario_run.steps
                      ],
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )


      @hookimpl(trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          if _run_context is None or _scenario_nodeid is None:
              return
          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          assert scenario_run is not None
          Path("tolerant-teardown-runtime.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "exception_type": type(scenario_run.exception).__name__ if scenario_run.exception else None,
                      "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
                      "runtime_status": _run_context.status,
                      "active_feature_binding": _run_context.active_feature_binding is not None,
                      "active_scenario_run": _run_context.active_scenario_run is not None,
                      "exit_status": int(exitstatus),
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/tolerant-teardown-interrupted-runtime.feature" contains:
      """gherkin
      Feature: Tolerant failure arbitration after teardown interruption
        Scenario: Tolerant failure stays failed while terminal pass becomes interrupted
          When the tolerant first step raises an AssertionError and continues
          Then the terminal scenario step completes successfully
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=tolerant-teardown-messages.ndjson --cuke-json=tolerant-teardown-report.json -q"
    Then pytest should exit with code 2
    And consumer runtime artifacts "tolerant-before-teardown.json", "tolerant-teardown-runtime.json", "tolerant-teardown-messages.ndjson" and "tolerant-teardown-report.json" should preserve the tolerant failure and interrupt sentinels

  Scenario: A teardown KeyboardInterrupt follows an undefined step with unstarted steps
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      from pytest import fixture, hookimpl
      from pytest_cuke import given, then


      _run_context = None
      _scenario_nodeid = None


      @fixture(autouse=True)
      def interrupting_teardown_after_undefined_step():
          yield
          raise KeyboardInterrupt("teardown after undefined-step sentinel")


      @given("the scenario arms teardown interruption before an undefined step")
      def scenario_arms_teardown_interrupt_before_undefined_step():
          pass


      @then("the middle runtime step remains unstarted")
      def middle_runtime_step_remains_unstarted():
          return "unreachable middle action"


      @then("the final runtime step remains unstarted")
      def final_runtime_step_remains_unstarted():
          return "unreachable final action"


      @hookimpl
      def pytest_cuke_before_scenario(request, run):
          global _run_context, _scenario_nodeid
          _run_context = request.getfixturevalue("run_context")
          _scenario_nodeid = request.node.nodeid


      @hookimpl
      def pytest_cuke_after_scenario(request, run):
          scenario_run = _run_context.active_scenario_run
          assert scenario_run is not None
          Path("undefined-before-teardown.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "step_names": [step_run.step.text for step_run in scenario_run.steps],
                      "step_statuses": [step_run.status for step_run in scenario_run.steps],
                      "step_exception_messages": [
                          str(step_run.exception) if step_run.exception is not None else None
                          for step_run in scenario_run.steps
                      ],
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )


      @hookimpl(trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          if _run_context is None or _scenario_nodeid is None:
              return
          scenario_run = _run_context.get_scenario_run(_scenario_nodeid)
          assert scenario_run is not None
          Path("undefined-teardown-runtime.json").write_text(
              json.dumps(
                  {
                      "scenario_status": scenario_run.status,
                      "exception_type": type(scenario_run.exception).__name__ if scenario_run.exception else None,
                      "exception_message": str(scenario_run.exception) if scenario_run.exception else None,
                      "runtime_status": _run_context.status,
                      "active_feature_binding": _run_context.active_feature_binding is not None,
                      "active_scenario_run": _run_context.active_scenario_run is not None,
                      "exit_status": int(exitstatus),
                  },
                  sort_keys=True,
              ),
              encoding="utf-8",
          )
      """
    And consumer file "features/undefined-teardown-interrupted-runtime.feature" contains:
      """gherkin
      Feature: Runtime reporting after an undefined step and teardown interruption
        Scenario: Teardown interruption follows an undefined step
          Given the scenario arms teardown interruption before an undefined step
          When an undefined runtime step is encountered
          Then the middle runtime step remains unstarted
          And the final runtime step remains unstarted
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=undefined-teardown-messages.ndjson --cuke-json=undefined-teardown-report.json -q"
    Then pytest should exit with code 2
    And consumer runtime artifacts "undefined-before-teardown.json", "undefined-teardown-runtime.json", "undefined-teardown-messages.ndjson" and "undefined-teardown-report.json" should preserve the undefined step and final teardown interruption
