Feature: Preventive guard for all-unmatched scenarios
  Explicit scenarios with steps but no matching definitions are rejected during
  collection unless the caller opts into skipping them.

  Scenario: Explicit all-unmatched bindings are rejected before execution by default
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def _record(name):
          with Path("preventive-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")
      """
    And consumer file "features/explicit-unmatched.feature" contains:
      """gherkin
      Feature: Explicit all-unmatched bindings
        Scenario: The explicit scenario has no matching definitions
          Given the first explicit step is unmatched
          When the second explicit step is unmatched
      """
    And consumer file "tests/test_explicit_unmatched.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("explicit-unmatched.feature", "The explicit scenario has no matching definitions")
      def test_explicit_unmatched_scenario():
          Path("pytest-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -q tests/test_explicit_unmatched.py"
    Then collection should reject consumer feature "features/explicit-unmatched.feature", scenario "The explicit scenario has no matching definitions", and step "the first explicit step is unmatched" before files "preventive-hooks.txt" and "pytest-body.txt" are created
    And pytest output should include "the second explicit step is unmatched"

  Scenario: Allow-empty CLI skips the same explicit all-unmatched case
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      testpaths = ["tests"]
      cuke_autoload = false
      cuke_features_dir = "features"
      cuke_parser = "python"
      cuke_allow_empty_scenarios = false
      """
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def _record(name):
          with Path("preventive-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")
      """
    And consumer file "features/explicit-unmatched.feature" contains:
      """gherkin
      Feature: Explicit all-unmatched bindings
        Scenario: The explicit scenario has no matching definitions
          Given the first explicit step is unmatched
          When the second explicit step is unmatched
      """
    And consumer file "tests/test_explicit_unmatched.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("explicit-unmatched.feature", "The explicit scenario has no matching definitions")
      def test_explicit_unmatched_scenario():
          Path("pytest-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-allow-empty-scenarios -rs -q tests/test_explicit_unmatched.py"
    Then pytest should skip all-unmatched scenario "The explicit scenario has no matching definitions" with a meaningful reason from feature "features/explicit-unmatched.feature" before files "preventive-hooks.txt" and "pytest-body.txt" are created
    And pytest output should include "No scenario step matched a step definition"

  Scenario: Allow-empty ini configuration skips an explicit all-unmatched case
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      testpaths = ["tests"]
      cuke_autoload = false
      cuke_features_dir = "features"
      cuke_parser = "python"
      cuke_allow_empty_scenarios = true
      """
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def _record(name):
          with Path("preventive-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      def pytest_cuke_before_scenario(request, run):
          _record("before-scenario")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("step-lookup-error")
      """
    And consumer file "features/explicit-unmatched.feature" contains:
      """gherkin
      Feature: Explicit all-unmatched bindings
        Scenario: The explicit scenario has no matching definitions
          Given the first explicit step is unmatched
          When the second explicit step is unmatched
      """
    And consumer file "tests/test_explicit_unmatched.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("explicit-unmatched.feature", "The explicit scenario has no matching definitions")
      def test_explicit_unmatched_scenario():
          Path("pytest-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -rs -q tests/test_explicit_unmatched.py"
    Then pytest should skip all-unmatched scenario "The explicit scenario has no matching definitions" with a meaningful reason from feature "features/explicit-unmatched.feature" before files "preventive-hooks.txt" and "pytest-body.txt" are created
    And pytest output should include "No scenario step matched a step definition"

  Scenario: Allow-empty does not relax strict empty-title validation
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given


      @given("the strict title control is matched")
      def strict_title_control_is_matched():
          Path("strict-title-body.txt").write_text("ran", encoding="utf-8")
      """
    And consumer file "features/strict-title.feature" contains:
      """gherkin
      Feature: Strict title boundary
        Scenario:
          Given the strict title control is matched
      """
    And consumer file "tests/test_strict_title.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("strict-title.feature", "")
      def test_empty_scenario_title():
          Path("strict-title-test-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-allow-empty-scenarios --cuke-strict -q tests/test_strict_title.py"
    Then pytest should exit with a non-zero code
    And pytest output should include "EMPTY_HEADING_TITLE"
    And pytest output should identify source "strict-title.feature" at the line containing "Scenario:" in consumer feature "features/strict-title.feature"
    And the consumer file "strict-title-body.txt" should not exist
    And the consumer file "strict-title-test-body.txt" should not exist

  Scenario: Partial matches bypass the guard and fail through normal step execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given


      def _record(name):
          with Path("partial-match-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @given("the inherited parent registry step is matched")
      def inherited_parent_registry_step():
          _record("parent-registry")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          _record("lookup-error")
      """
    And consumer file "features/partial-match.feature" contains:
      """gherkin
      Feature: Partial step matches
        Scenario: One step is inherited and another is missing
          Given the inherited parent registry step is matched
          And the local child registry step is matched
          When the unmatched partial step is absent
      """
    And consumer file "tests/test_partial_match.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given, scenario


      @given("the local child registry step is matched")
      def local_child_registry_step():
          with Path("partial-match-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write("child-registry\n")


      @scenario("partial-match.feature", "One step is inherited and another is missing")
      def test_partial_match_reaches_runtime():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -q tests/test_partial_match.py"
    Then pytest should exit with a non-zero code
    And pytest output should include "Step definition is not found"
    And pytest output should include "the unmatched partial step is absent"
    And pytest output should not include "UsageError"
    And consumer marker file "partial-match-markers.txt" should contain lines "parent-registry,child-registry,lookup-error"

  Scenario: A fully matched explicit scenario inherits exact, parsed, regex, and expression bindings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given


      def _record(name):
          with Path("registry-body-calls.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @given("the inherited exact step is bound", target_fixture="inherited_value")
      def inherited_exact_step():
          _record("parent-exact")
          return "from parent conftest"
      """
    And consumer file "features/matched-registry.feature" contains:
      """gherkin
      Feature: Fully matched registries
        Scenario: Parent exact and local matcher definitions are matched
          Given the inherited exact step is bound
          When the local parsed step captures 41
          And the local regex matcher captures 42
          And the local expression matcher captures 43
          Then the inherited, parsed, regex, and expression values are available
      """
    And consumer file "tests/test_matched_registry.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import parsers, scenario, then, when


      def _record(name):
          with Path("registry-body-calls.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      @when(parsers.parse("the local parsed step captures {value:d}"), target_fixture="parsed_value")
      def local_parse_step(value):
          _record("module-parse")
          return value


      @when(parsers.re(r"^the local regex matcher captures (?P<value>\d+)$"), target_fixture="regex_value")
      def local_regex_matcher(value):
          _record("module-regex")
          return int(value)


      @when(
          parsers.cucumber_expression("the local expression matcher captures {int}"),
          target_fixture="expression_value",
          anonymous_group_names=["value"],
      )
      def local_expression_matcher(value):
          _record("module-expression")
          return value


      @then("the inherited, parsed, regex, and expression values are available")
      def verify_registry_values(inherited_value, parsed_value, regex_value, expression_value):
          assert inherited_value == "from parent conftest"
          assert parsed_value == 41
          assert regex_value == 42
          assert expression_value == 43


      @scenario("matched-registry.feature", "Parent exact and local matcher definitions are matched")
      def test_fully_matched_registry():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -q tests/test_matched_registry.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer marker file "registry-body-calls.txt" should contain lines "parent-exact,module-parse,module-regex,module-expression"

  Scenario: A nonempty keyword filter bypasses unmatched scenarios independently
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      testpaths = ["tests"]
      cuke_autoload = false
      cuke_features_dir = "features"
      cuke_parser = "python"
      markers = [
        "selected_validation: selected scenarios for the empty binding guard",
        "excluded_validation: scenarios excluded by the marker filter",
      ]
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the selected guard control is bound")
      def selected_guard_control_is_bound():
          pass
      """
    And consumer file "features/filter-unmatched.feature" contains:
      """gherkin
      Feature: Selection filters and unmatched scenarios
        Scenario: The selected guard control is bound
          Given the selected guard control is bound

        Scenario: The keyword filter excludes this unmatched case
          Given the keyword-excluded step has no definition

        Scenario: The marker filter excludes this unmatched case
          Given the marker-excluded step has no definition
      """
    And consumer file "tests/test_filter_unmatched.py" contains:
      """python
      import pytest
      from pytest_cuke import scenario


      @pytest.mark.selected_validation
      @scenario("filter-unmatched.feature", "The selected guard control is bound")
      def test_selected_guard_control():
          pass


      @scenario("filter-unmatched.feature", "The keyword filter excludes this unmatched case")
      def test_excluded_by_keyword():
          pass


      @pytest.mark.excluded_validation
      @scenario("filter-unmatched.feature", "The marker filter excludes this unmatched case")
      def test_excluded_by_keyword_only():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload -k test_selected_guard -q tests/test_filter_unmatched.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And pytest output should report exactly 2 deselected items

  Scenario: A nonempty marker filter bypasses unmatched scenarios independently
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      testpaths = ["tests"]
      cuke_autoload = false
      cuke_features_dir = "features"
      cuke_parser = "python"
      markers = [
        "selected_validation: selected scenarios for the empty binding guard",
        "excluded_validation: scenarios excluded by the marker filter",
      ]
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the selected guard control is bound")
      def selected_guard_control_is_bound():
          pass
      """
    And consumer file "features/filter-unmatched.feature" contains:
      """gherkin
      Feature: Selection filters and unmatched scenarios
        Scenario: The selected guard control is bound
          Given the selected guard control is bound

        Scenario: The keyword filter excludes this unmatched case
          Given the keyword-excluded step has no definition

        Scenario: The marker filter excludes this unmatched case
          Given the marker-excluded step has no definition
      """
    And consumer file "tests/test_filter_unmatched.py" contains:
      """python
      import pytest
      from pytest_cuke import scenario


      @pytest.mark.selected_validation
      @scenario("filter-unmatched.feature", "The selected guard control is bound")
      def test_selected_guard_control():
          pass


      @scenario("filter-unmatched.feature", "The keyword filter excludes this unmatched case")
      def test_unmatched_without_marker():
          pass


      @pytest.mark.excluded_validation
      @scenario("filter-unmatched.feature", "The marker filter excludes this unmatched case")
      def test_unmatched_with_other_marker():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload -m selected_validation -q tests/test_filter_unmatched.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And pytest output should report exactly 2 deselected items

  Scenario: Autoloaded all-unmatched scenarios retain normal runtime missing-step behavior
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def pytest_cuke_before_scenario(request, run):
          Path("autoload-runtime-hooks.txt").write_text("before-scenario", encoding="utf-8")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          with Path("autoload-runtime-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write("\nstep-lookup-error")
      """
    And consumer file "features/autoload-unmatched.feature" contains:
      """gherkin
      Feature: Autoload all-unmatched scenario
        Scenario: The autoloaded scenario has no matching definitions
          Given the first autoloaded step is unmatched
          When the second autoloaded step is unmatched
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "Step definition is not found"
    And pytest output should include "the first autoloaded step is unmatched"
    And pytest output should not include "UsageError"
    And consumer marker file "autoload-runtime-hooks.txt" should contain lines "before-scenario,step-lookup-error"

  Scenario: Autoloaded all-unmatched scenarios retain mock-run binding diagnostics
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def pytest_cuke_before_scenario(request, run):
          Path("autoload-mock-run-hooks.txt").write_text("before-scenario", encoding="utf-8")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          with Path("autoload-mock-run-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write("\nstep-lookup-error")
      """
    And consumer file "features/autoload-mock-unmatched.feature" contains:
      """gherkin
      Feature: Autoload mock-run binding validation
        Scenario: The autoloaded mock-run scenario has no definitions
          Given the first autoloaded mock-run step is unmatched
          When the second autoloaded mock-run step is unmatched
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "the first autoloaded mock-run step is unmatched"
    And pytest output should include "the second autoloaded mock-run step is unmatched"
    And pytest output should not include "UsageError"
    And the consumer file "autoload-mock-run-hooks.txt" should not exist

  Scenario: Zero-step explicit scenarios are not treated as all-unmatched
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/zero-step.feature" contains:
      """gherkin
      Feature: Zero-step scenario control
        Scenario: This scenario contains no steps
      """
    And consumer file "tests/test_zero_step.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("zero-step.feature", "This scenario contains no steps")
      def test_zero_step_scenario():
          Path("zero-step-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python -q tests/test_zero_step.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And the consumer file "zero-step-body.txt" should exist

  Scenario: Mock run remains excluded from the preventive all-unmatched guard
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def pytest_cuke_before_scenario(request, run):
          Path("mock-run-runtime-hooks.txt").write_text("before-scenario", encoding="utf-8")


      def pytest_cuke_step_func_lookup_error(request, run, exception):
          with Path("mock-run-runtime-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write("\nstep-lookup-error")
      """
    And consumer file "features/mock-run-unmatched.feature" contains:
      """gherkin
      Feature: Mock run all-unmatched scenario
        Scenario: Mock run reports every unmatched step
          Given the first mock-run step is unmatched
          When the second mock-run step is unmatched
      """
    And consumer file "tests/test_mock_run_unmatched.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("mock-run-unmatched.feature", "Mock run reports every unmatched step")
      def test_mock_run_unmatched_scenario():
          Path("mock-run-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-mock-run -q tests/test_mock_run_unmatched.py"
    Then pytest should exit with a non-zero code
    And pytest output should include "the first mock-run step is unmatched"
    And pytest output should include "the second mock-run step is unmatched"
    And pytest output should not include "UsageError"
    And the consumer file "mock-run-runtime-hooks.txt" should not exist
    And the consumer file "mock-run-body.txt" should not exist

  Scenario: Missing-step generation reports unmatched diagnostics before normal collection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/generation-unmatched.feature" contains:
      """gherkin
      Feature: Generation owns unmatched diagnostics
        Scenario: The generator reports this missing step
          Given the step generated in generation mode is missing
      """
    And consumer file "tests/test_generation_unmatched.py" contains:
      """python
      from pytest_cuke import scenario


      @scenario("generation-unmatched.feature", "The generator reports this missing step")
      def test_generation_target():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-generate-missing --cuke-feature=features/generation-unmatched.feature -q tests/test_generation_unmatched.py"
    Then pytest should exit with code 0
    And pytest output should include "the step generated in generation mode is missing"
    And pytest output should include "Please place the code above to the test file(s):"
    And pytest output should not include "UsageError"

  Scenario: Full generation mode owns its unmatched-step output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/generation-code.feature" contains:
      """gherkin
      Feature: Full generation owns unmatched scenarios
        Scenario: The generation code is missing
          Given the generation-owned step is missing
      """
    And consumer file "tests/test_generation_code.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("generation-code.feature", "The generation code is missing")
      def test_generation_code_target():
          Path("generation-code-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest from consumer directory "." with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-generate --cuke-feature={consumer_path}/features/generation-code.feature -q tests/test_generation_code.py"
    Then pytest should exit with code 0
    And pytest output should include "the generation-owned step is missing"
    And pytest output should include "raise NotImplementedError"
    And pytest output should not include "UsageError"
    And the consumer file "generation-code-body.txt" should not exist

  Scenario: Consecutive pytest sessions do not reuse a previous module registry
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "first/features/session-registry.feature" contains:
      """gherkin
      Feature: First session registry
        Scenario: The shared step is bound
          Given the session registry step is shared
      """
    And consumer file "first/tests/test_first_registry.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given, scenario


      @given("the session registry step is shared")
      def session_registry_step_is_shared():
          Path("first-session-step-calls.txt").write_text("first-session", encoding="utf-8")


      @scenario("session-registry.feature", "The shared step is bound")
      def test_first_session_registry():
          pass
      """
    And consumer file "second/features/session-registry.feature" contains:
      """gherkin
      Feature: Second session registry
        Scenario: The shared step is bound
          Given the session registry step is shared
      """
    And consumer file "second/tests/test_second_registry.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import scenario


      @scenario("session-registry.feature", "The shared step is bound")
      def test_second_session_registry():
          Path("second-session-body.txt").write_text("ran", encoding="utf-8")
      """
    When I run installed pytest twice in one process with arguments "--rootdir=first --cuke-no-autoload --cuke-parser=python --cuke-features-dir=features -q first/tests/test_first_registry.py" and then "--rootdir=second --cuke-no-autoload --cuke-parser=python --cuke-features-dir=features -q second/tests/test_second_registry.py"
    Then consumer repeated pytest sessions should exit with codes "0,4"
    And pytest output should include "ERROR: Explicit scenarios with steps but no matching step definitions were found"
    And pytest output should identify source "second/features/session-registry.feature" at the line containing "Given the session registry step is shared" in consumer feature "second/features/session-registry.feature"
    And pytest output should include "the session registry step is shared"
    And consumer marker file "first-session-step-calls.txt" should contain lines "first-session"
    And the consumer file "second-session-body.txt" should not exist
