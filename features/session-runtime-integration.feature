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
      def pytest_cuke_before_scenario(request, feature, scenario):
          _snapshot(request.getfixturevalue("run_context"), "pytest_cuke_before_scenario")


      @hookimpl
      def pytest_cuke_before_step(request, feature, scenario, step, step_func):
          _snapshot(request.getfixturevalue("run_context"), "pytest_cuke_before_step")


      @hookimpl
      def pytest_cuke_after_scenario(request, feature, scenario):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=runtime-sequence.ndjson --cuke-summary -q"
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
      def pytest_cuke_before_scenario(request, feature, scenario):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with code 1
    And consumer runtime artifact "runtime-cleanup-observations.jsonl" should show failed teardown then clean BDD state
    And consumer runtime snapshot "plain-after-bdd-observation.json" should show clean plain pytest state after BDD teardown

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
      def pytest_cuke_before_scenario(request, feature, scenario):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=runtime-terminal-outcomes.ndjson --cuke-summary -q"
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
              "pickle_id": scenario_run.scenario.id,
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=rule-runtime.ndjson --cuke-json=rule-runtime.json --cuke-summary -q"
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
      def pytest_cuke_before_scenario(request, feature, scenario):
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
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=xdist-runtime.ndjson -n2 --dist=loadfile --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer xdist runtime artifacts should show separate run roots in "xdist-runtime.ndjson"
