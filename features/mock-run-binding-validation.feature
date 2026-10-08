Feature: Binding-only mock run validation
  Consumers can validate scenario bindings without running BDD hooks or step bodies.
  Mock run still imports consumer modules, collects and selects pytest items, runs
  collection/plugin work, and calls the selected pytest item function. It is not
  globally side-effect-free; only BDD lifecycle hooks and step bodies are skipped.

  Scenario: Mock run skips BDD execution but retains ordinary pytest function execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has no Allure Python adapters or Node on PATH
    And consumer file "conftest.py" contains:
      """python
      from functools import wraps
      from pathlib import Path

      from pytest_cuke import given


      def _record(name):
          with Path("mock-run-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @given("the bound step body records its execution")
      def bound_step_body_records_execution():
          _record("step-body")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_run_scenario(request, run):
          _record("run-scenario")


      def pytest_cuke_after_scenario(request, run):
          _record("after-scenario")


      def pytest_cuke_before_step(request, run, step_func):
          _record("before-step")


      def pytest_cuke_before_step_call(request, run, step_func, step_func_args, step_definition):
          _record("before-step-call")


      def pytest_cuke_after_step(request, run, step_func, step_func_args, step_definition):
          _record("after-step")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")


      def pytest_cuke_step_error(request, run, step_func, step_func_args, exception, step_definition, tolerated=False):
          _record("step-error")


      def _track_test_function(test_function):
          @wraps(test_function)
          def record_test_function_body(*args, **kwargs):
              _record("test-function-body")
              return test_function(*args, **kwargs)

          return record_test_function_body


      def pytest_collection_modifyitems(items):
          for item in items:
              if "pytest_cuke_scenario" in item.keywords:
                  item.obj = _track_test_function(item.obj)
      """
    And consumer file "features/mock-run.feature" contains:
      """gherkin
      Feature: Mock run binding validation
        Scenario: Every step binding is present
          Given the bound step body records its execution
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer marker artifact "mock-run-markers.txt" should contain the normal BDD execution markers
    When I remove consumer file "mock-run-markers.txt"
    And I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer marker artifact "mock-run-markers.txt" should contain only 1 instance of the pytest test-function body marker

  Scenario: Multiple missing bindings fail validation before BDD execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from functools import wraps
      from pathlib import Path

      from pytest_cuke import given


      def _record(name):
          with Path("mock-run-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @given("the bound step body records its execution")
      def bound_step_body_records_execution():
          _record("step-body")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_run_scenario(request, run):
          _record("run-scenario")


      def pytest_cuke_after_scenario(request, run):
          _record("after-scenario")


      def pytest_cuke_before_step(request, run, step_func):
          _record("before-step")


      def pytest_cuke_before_step_call(request, run, step_func, step_func_args, step_definition):
          _record("before-step-call")


      def pytest_cuke_after_step(request, run, step_func, step_func_args, step_definition):
          _record("after-step")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")


      def pytest_cuke_step_error(request, run, step_func, step_func_args, exception, step_definition, tolerated=False):
          _record("step-error")


      def _track_test_function(test_function):
          @wraps(test_function)
          def record_test_function_body(*args, **kwargs):
              _record("test-function-body")
              return test_function(*args, **kwargs)

          return record_test_function_body


      def pytest_collection_modifyitems(items):
          for item in items:
              if "pytest_cuke_scenario" in item.keywords:
                  item.obj = _track_test_function(item.obj)
      """
    And consumer file "features/missing-bindings.feature" contains:
      """gherkin
      Feature: Missing mock run bindings
        Scenario: All missing steps are reported together
          Given the bound step body records its execution
          And the missing binding probe alpha is absent
          And the missing binding probe beta is absent
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "the missing binding probe alpha is absent"
    And pytest output should include "the missing binding probe beta is absent"
    And the consumer file "mock-run-markers.txt" should not exist

  Scenario: Explicit all-missing binding validation reports every step
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from functools import wraps
      from pathlib import Path


      def _record(name):
          with Path("mock-run-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_run_scenario(request, run):
          _record("run-scenario")


      def pytest_cuke_after_scenario(request, run):
          _record("after-scenario")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")


      def pytest_cuke_step_error(request, run, step_func, step_func_args, exception, step_definition, tolerated=False):
          _record("step-error")


      def _track_test_function(test_function):
          @wraps(test_function)
          def record_test_function_body(*args, **kwargs):
              _record("test-function-body")
              return test_function(*args, **kwargs)

          return record_test_function_body


      def pytest_collection_modifyitems(items):
          for item in items:
              if "pytest_cuke_scenario" in item.keywords:
                  item.obj = _track_test_function(item.obj)
      """
    And consumer file "features/explicit-missing.feature" contains:
      """gherkin
      Feature: Explicit all-missing mock run bindings
        Scenario: Every step is unbound
          Given the missing explicit binding first is absent
          When the missing explicit binding second is absent
          Then the missing explicit binding third is absent
      """
    And consumer file "tests/test_explicit_missing_bindings.py" contains:
      """python
      from pytest_cuke import scenario


      @scenario("explicit-missing.feature", "Every step is unbound")
      def test_explicit_all_missing_bindings():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "the missing explicit binding first is absent"
    And pytest output should include "the missing explicit binding second is absent"
    And pytest output should include "the missing explicit binding third is absent"
    And pytest output should not include "UsageError"
    And the consumer file "mock-run-markers.txt" should not exist

  Scenario: INI mock run validates explicit outline bindings after pytest selection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      testpaths = ["tests"]
      cuke_autoload = false
      cuke_features_dir = "features"
      cuke_parser = "python"
      cuke_mock_run = true
      markers = [
        "mock_validation: scenarios selected for binding validation",
        "excluded_validation: scenarios excluded from binding validation",
      ]
      """
    And consumer file "conftest.py" contains:
      """python
      from functools import wraps
      from pathlib import Path

      from pytest_cuke import given, parsers, when


      def _record(name):
          with Path("mock-run-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @given("the feature background opens the account")
      def feature_background_opens_account():
          _record("step-body")


      @given("the rule background prepares the ledger")
      def rule_background_prepares_ledger():
          _record("step-body")


      @given(parsers.parse("the selected account is {account}"))
      def selected_account_is(account):
          _record("step-body")


      @when(parsers.parse("I request {action} for account {account}"))
      def request_action(action, account):
          _record("step-body")


      @when(parsers.parse("the validation outcome is {outcome} for account {account}"))
      def validation_outcome_is(outcome, account):
          _record("step-body")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_run_scenario(request, run):
          _record("run-scenario")


      def pytest_cuke_after_scenario(request, run):
          _record("after-scenario")


      def pytest_cuke_before_step(request, run, step_func):
          _record("before-step")


      def pytest_cuke_before_step_call(request, run, step_func, step_func_args, step_definition):
          _record("before-step-call")


      def pytest_cuke_after_step(request, run, step_func, step_func_args, step_definition):
          _record("after-step")


      def pytest_cuke_step_error(request, run, step_func, step_func_args, exception, step_definition, tolerated=False):
          _record("step-error")


      def _track_test_function(test_function):
          @wraps(test_function)
          def record_test_function_body(*args, **kwargs):
              _record("test-function-body")
              return test_function(*args, **kwargs)

          return record_test_function_body


      def pytest_collection_modifyitems(items):
          for item in items:
              if "pytest_cuke_scenario" in item.keywords:
                  item.obj = _track_test_function(item.obj)


      def pytest_collection_finish(session):
          Path("collected-nodeids.txt").write_text(
              "\n".join(item.nodeid for item in session.items) + "\n",
              encoding="utf-8",
          )
      """
    And consumer file "features/explicit-mock-run.feature" contains:
      """gherkin
      Feature: Explicit mock-run binding selection
        Background:
          Given the feature background opens the account

        Rule: Selected account request
          Background:
            Given the rule background prepares the ledger

          @mock_validation
          Scenario Outline: The selected account path is binding-valid
            And the selected account is <account>
            When I request <action> for account <account>
            And the validation outcome is <outcome> for account <account>

            Examples:
              | account | action | outcome  |
              | amber   | expand | expanded |
              | birch   | focus  | focused  |

        @mock_validation
        Scenario: The keyword filter excludes this missing binding
          Given the missing keyword-filtered binding is absent

        @excluded_validation
        Scenario: The marker filter excludes this missing binding
          Given the missing marker-filtered binding is absent
      """
    And consumer file "tests/test_explicit_mock_run.py" contains:
      """python
      from pytest_cuke import scenario


      @scenario("explicit-mock-run.feature", "The selected account path is binding-valid")
      def test_selected_outline_validation():
          pass


      @scenario("explicit-mock-run.feature", "The keyword filter excludes this missing binding")
      def test_keyword_filtered_out():
          pass


      @scenario("explicit-mock-run.feature", "The marker filter excludes this missing binding")
      def test_selected_outline_validation_but_marker_filtered():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload -k test_selected_outline_validation -m mock_validation --cuke-messages-ndjson=selected-outline.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And pytest output should not include "the missing keyword-filtered binding is absent"
    And pytest output should not include "the missing marker-filtered binding is absent"
    And consumer marker artifact "mock-run-markers.txt" should contain only 2 instances of the pytest test-function body marker
    And consumer artifact "selected-outline.ndjson" should preserve mock-run background and row binding arguments

  Scenario: Mock run Messages retain bound and missing source identities
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given


      def _record(name):
          with Path("mock-run-failure-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @given("the IDE mock-run match is available")
      def ide_mock_run_match_is_available():
          raise AssertionError("mock-run must not execute step bodies")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")


      def pytest_cuke_step_error(request, run, step_func, step_func_args, exception, step_definition, tolerated=False):
          _record("step-error")


      def pytest_collection_finish(session):
          Path("collected-nodeids.txt").write_text(
              "\n".join(item.nodeid for item in session.items) + "\n",
              encoding="utf-8",
          )
      """
    And consumer file "features/mock-run-messages.feature" contains:
      """gherkin
      Feature: Mock-run IDE binding messages
        Scenario: The bound message step is validated
          Given the IDE mock-run match is available

        Scenario: Missing message steps are diagnosed together
          Given the first missing IDE message step is absent
          When the second missing IDE message step is absent
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run --cuke-messages-ndjson=mock-run.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "the first missing IDE message step is absent"
    And pytest output should include "the second missing IDE message step is absent"
    And consumer artifact "mock-run.ndjson" should link mock-run launches to bound and missing source identities
    And the consumer file "mock-run-failure-hooks.txt" should not exist

  Scenario: Repeated mock run sessions keep xdist source and binding identities isolated
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import json
      import os
      from pathlib import Path

      from pytest_cuke import given, parsers


      @given(parsers.parse("the worker source is {value}"))
      def worker_source_is(value):
          Path("mock-run-execution.txt").write_text("step-body", encoding="utf-8")
          raise AssertionError(f"mock-run executed the step body for {value}")


      def pytest_cuke_before_scenario(request, run):
          Path("mock-run-execution.txt").write_text("before-scenario", encoding="utf-8")


      def pytest_runtest_call(item):
          observation = {
              "nodeid": item.nodeid,
              "worker": os.environ.get("PYTEST_XDIST_WORKER", "main"),
          }
          with Path("worker-nodeids.ndjson").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(observation) + "\n")
      """
    And consumer file "features/first-session/north-source.feature" contains:
      """gherkin
      Feature: First mock run session
        Scenario: The north source is collected
          Given the worker source is north
      """
    And consumer file "features/second-session/north-source.feature" contains:
      """gherkin
      Feature: North mock run worker
        Scenario: The north source is collected
          Given the worker source is north
      """
    And consumer file "features/second-session/south-source.feature" contains:
      """gherkin
      Feature: South mock run worker
        Scenario: The south source is collected
          Given the worker source is south
      """
    When I run installed pytest twice in one process with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features/first-session --cuke-mock-run --cuke-messages-ndjson=first-mock-run.ndjson -q features/first-session" and then "--rootdir=. features/second-session --cuke-autoload --cuke-parser=python --cuke-features-dir=features/second-session --cuke-mock-run --cuke-messages-ndjson=second-mock-run.ndjson -n2 --dist=loadfile -q"
    Then consumer repeated pytest sessions should exit with codes "0,0"
    And consumer artifacts "first-mock-run.ndjson" and "second-mock-run.ndjson" should preserve mock-run session and worker identities
    And the consumer file "mock-run-execution.txt" should not exist
