Feature: Installed pytest-cuke product bootstrap
  A consumer installs the public package, discovers its pytest plugin, and uses
  the canonical pytest-cuke commands and configuration without harness imports.

  Scenario Outline: A built distribution exposes only the canonical root facade
    Given the pytest-cuke <distribution> built from this checkout is installed in a fresh consumer project
    And consumer file "test_public_api.py" contains:
      """python
      import importlib.metadata
      import importlib.util
      from pathlib import PurePosixPath

      import pytest_cuke
      from pytest_cuke import *

      PUBLIC_NAMES = {"given", "when", "then", "step", "parsers", "scenario", "scenarios"}


      def test_installed_public_facade():
          distribution = importlib.metadata.distribution("pytest-cuke")
          assert distribution.version
          assert set(pytest_cuke.__all__) == PUBLIC_NAMES
          assert {name for name in globals() if name in PUBLIC_NAMES} == PUBLIC_NAMES
          assert all(callable(getattr(pytest_cuke, name)) for name in PUBLIC_NAMES - {"parsers"})
          assert all(hasattr(parsers, name) for name in ("parse", "re", "cfparse", "cuke_expressions"))
          assert all(not hasattr(pytest_cuke, name) for name in ("Feature", "Scenario", "Step", "Pickle", "Runner"))
          assert importlib.util.find_spec("pytest_bdd") is None
          assert importlib.util.find_spec("allure_pytest") is None
          assert all(importlib.util.find_spec(name) is None for name in ("yaml", "hjson", "json5", "pyhocon"))

          files = distribution.files or ()
          harness_assets = {".planning", ".agents", "pytest_cuke_testing", "tests", "features", "examples"}
          assert not any(harness_assets.intersection(PurePosixPath(str(path)).parts) for path in files)
      """
    When I run installed pytest with arguments "--rootdir=. test_public_api.py -q"
    Then pytest should exit with code 0
    And the installed distribution archive excludes harness and test assets

    Examples:
      | distribution     |
      | wheel            |
      | sdist            |

  Scenario: Plugin autoload runs a Background and a two-row Outline through the facade
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest import fixture
      from pytest_cuke import given, parsers, then, when


      @fixture
      def seed_value():
          return 40


      @given("the canonical pytest plugin is loaded once")
      def canonical_plugin_is_loaded_once(pytestconfig):
          plugins = [
              plugin
              for name, plugin in pytestconfig.pluginmanager.list_name_plugin()
              if name == "cuke"
          ]
          assert len(plugins) == 1
          assert plugins[0].__name__ == "pytest_cuke.plugin"


      @given("the shared pytest fixture is active")
      def shared_fixture_is_active(seed_value):
          assert seed_value == 40


      @when(parsers.parse("I add {amount:d} to the seed value"), target_fixture="total")
      def add_to_seed(seed_value, amount):
          return seed_value + amount


      @then(parsers.parse("the total is {expected:d}"))
      def check_total(total, expected):
          assert total == expected
      """
    And consumer file "features/fixture-outline.feature" contains:
      """gherkin
      Feature: Installed consumer scenarios
        Background:
          Given the canonical pytest plugin is loaded once
          Given the shared pytest fixture is active

        Scenario Outline: A parsed step can produce a target fixture
          When I add <amount> to the seed value
          Then the total is <expected>

          Examples:
            | amount | expected |
            | 2      | 42       |
            | 5      | 45       |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload --cuke-json=report.json --cuke-summary --cuke-progress"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And pytest terminal output should report 2 passed BDD scenarios
    And consumer artifact "report.json" should describe one feature with 2 passed scenarios

  Scenario: NDJSON reports a no-Background scenario after plugin autoload
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers, then


      @given(parsers.parse("the value is {value:d}"), target_fixture="number")
      def value_is(value):
          return value


      @then(parsers.parse("the result is {expected:d}"))
      def result_is(number, expected):
          assert number == expected
      """
    And consumer file "features/messages.feature" contains:
      """gherkin
      Feature: Messages output
        Scenario: The stream describes an executed scenario
          Given the value is 42
          Then the result is 42
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload --cuke-messages-ndjson=messages.ndjson --cuke-summary"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 2 passed steps

  Scenario: Pytest reports invalid canonical option values
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir="
    Then pytest should exit with a non-zero code
    And pytest output should explain the invalid feature directory

  Scenario: A command-line feature directory overrides the canonical config value
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "configured-features"
      cuke_autoload = true
      cuke_summary = true
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the command-line feature was selected")
      def command_line_feature_selected():
          pass


      @given("the configuration-only feature was selected")
      def configuration_only_feature_selected():
          raise AssertionError("pytest ignored --cuke-features-dir")
      """
    And consumer file "configured-features/configured.feature" contains:
      """gherkin
      Feature: Configured feature directory
        Scenario: This feature must be overridden
          Given the configuration-only feature was selected
      """
    And consumer file "cli-features/selected.feature" contains:
      """gherkin
      Feature: Command-line feature directory
        Scenario: The CLI value takes precedence
          Given the command-line feature was selected
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=cli-features"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: Legacy pytest-bdd imports and option spellings are rejected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "test_legacy_import.py" contains:
      """python
      import importlib.util


      def test_legacy_package_is_not_installed():
          assert importlib.util.find_spec("pytest_bdd") is None
      """
    When I run installed pytest with arguments "--rootdir=. --help"
    Then pytest should exit with code 0
    And pytest help should not mention the legacy option "cucumber-json"
    And pytest help should not mention the legacy option "cucumber-html"
    And pytest help should not mention the legacy option "messages-ndjson"
    And pytest help should not mention the legacy option "disable-feature-autoload"
    And pytest help should not mention the legacy option "liberal-steps"
    And pytest help should not mention the legacy option "gherkin-terminal-reporter"
    And pytest help should not mention the legacy option "generate"
    And pytest help should not mention the legacy option "generate-missing"
    And pytest help should not mention the legacy option "feature"
    When I run installed pytest with arguments "--rootdir=. test_legacy_import.py -q"
    Then pytest should exit with code 0

  Scenario Outline: Both installed command names report the package version
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run command "<command>" with arguments "--version"
    Then the command should exit with code 0
    And the command output should identify the installed pytest-cuke version

    Examples:
      | command     |
      | pytest-cuke |
      | cuke        |

  Scenario: Standalone dispatchers show commands and reject unimplemented work honestly
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run command "cuke" with arguments "--help"
    Then the command should exit with code 0
    And the command output should list the public subcommands
    When I run command "pytest-cuke" with arguments "--help"
    Then the command should exit with code 0
    And the command output should list the public subcommands
    When I run command "cuke" with arguments "validate --help"
    Then the command should exit with code 0
    And the command help should show the required feature-directory argument
    When I run command "cuke" with arguments "validate"
    Then the command should exit with a non-zero code
    And the command output should require a feature directory
    When I run command "cuke" with arguments "validate consumer-features"
    Then the command should exit with a non-zero code
    And the unimplemented command should report that it is not implemented
    When I run command "cuke" with arguments "generate steps"
    Then the command should exit with a non-zero code
    And the unimplemented command should report that it is not implemented
    When I run command "cuke" with arguments "convert allure"
    Then the command should exit with a non-zero code
    And the unimplemented command should report that it is not implemented
