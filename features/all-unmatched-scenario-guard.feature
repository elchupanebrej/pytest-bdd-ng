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


      def pytest_cuke_before_scenario(request, feature, scenario):
          _record("before-scenario")


      def pytest_cuke_step_func_lookup_error(request, feature, scenario, step, exception):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-summary -q tests/test_explicit_unmatched.py"
    Then collection should reject consumer feature "features/explicit-unmatched.feature", scenario "The explicit scenario has no matching definitions", and step "the first explicit step is unmatched" before files "preventive-hooks.txt" and "pytest-body.txt" are created

  Scenario: Allow-empty CLI skips the same explicit all-unmatched case
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def _record(name):
          with Path("preventive-hooks.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      def pytest_cuke_before_scenario(request, feature, scenario):
          _record("before-scenario")


      def pytest_cuke_step_func_lookup_error(request, feature, scenario, step, exception):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-allow-empty-scenarios --cuke-summary -rs -q tests/test_explicit_unmatched.py"
    Then pytest should skip all-unmatched scenario "The explicit scenario has no matching definitions" with a meaningful reason before files "preventive-hooks.txt" and "pytest-body.txt" are created

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


      def pytest_cuke_before_scenario(request, feature, scenario):
          _record("before-scenario")


      def pytest_cuke_step_func_lookup_error(request, feature, scenario, step, exception):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-summary -rs -q tests/test_explicit_unmatched.py"
    Then pytest should skip all-unmatched scenario "The explicit scenario has no matching definitions" with a meaningful reason before files "preventive-hooks.txt" and "pytest-body.txt" are created

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


      def pytest_cuke_step_func_lookup_error(request, feature, scenario, step, exception):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-summary -q tests/test_partial_match.py"
    Then pytest should exit with a non-zero code
    And pytest output should include "Step definition is not found"
    And pytest output should include "the unmatched partial step is absent"
    And pytest output should not include "UsageError"
    And consumer marker file "partial-match-markers.txt" should contain lines "parent-registry,child-registry,lookup-error"

  Scenario: A fully matched explicit scenario inherits exact and parsed local bindings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the inherited exact step is bound", target_fixture="inherited_value")
      def inherited_exact_step():
          return "from parent conftest"
      """
    And consumer file "features/matched-registry.feature" contains:
      """gherkin
      Feature: Fully matched registries
        Scenario: Parent exact and local parse definitions are matched
          Given the inherited exact step is bound
          When the local parsed step captures 41
          Then the inherited and parsed values are available
      """
    And consumer file "tests/test_matched_registry.py" contains:
      """python
      from pytest_cuke import parsers, scenario, then, when


      @when(parsers.parse("the local parsed step captures {value:d}"), target_fixture="parsed_value")
      def local_parse_step(value):
          return value


      @then("the inherited and parsed values are available")
      def verify_registry_values(inherited_value, parsed_value):
          assert inherited_value == "from parent conftest"
          assert parsed_value == 41


      @scenario("matched-registry.feature", "Parent exact and local parse definitions are matched")
      def test_fully_matched_registry():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-summary -q tests/test_matched_registry.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload -k test_selected_guard --cuke-summary -q tests/test_filter_unmatched.py"
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload -m selected_validation --cuke-summary -q tests/test_filter_unmatched.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And pytest output should report exactly 2 deselected items

  Scenario: Autoloaded all-unmatched scenarios retain normal runtime missing-step behavior
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def pytest_cuke_before_scenario(request, feature, scenario):
          Path("autoload-runtime-hooks.txt").write_text("before-scenario", encoding="utf-8")


      def pytest_cuke_step_func_lookup_error(request, feature, scenario, step, exception):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "Step definition is not found"
    And pytest output should include "the first autoloaded step is unmatched"
    And pytest output should not include "UsageError"
    And consumer marker file "autoload-runtime-hooks.txt" should contain lines "before-scenario,step-lookup-error"

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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-summary -q tests/test_zero_step.py"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And the consumer file "zero-step-body.txt" should exist

  Scenario: Mock run remains excluded from the preventive all-unmatched guard
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path


      def pytest_cuke_before_scenario(request, feature, scenario):
          Path("mock-run-runtime-hooks.txt").write_text("before-scenario", encoding="utf-8")


      def pytest_cuke_step_func_lookup_error(request, feature, scenario, step, exception):
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-mock-run --cuke-summary -q tests/test_mock_run_unmatched.py"
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
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-generate-missing --cuke-feature=features/generation-unmatched.feature --cuke-summary -q tests/test_generation_unmatched.py"
    Then pytest should exit with code 0
    And pytest output should include "the step generated in generation mode is missing"
    And pytest output should include "Please place the code above to the test file(s):"
    And pytest output should not include "UsageError"
