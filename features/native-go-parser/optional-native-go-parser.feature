Feature: Optional native Go parser and Python fallback
  Consumers can choose the pure-Python parser, use automatic fallback, or require
  native support through the canonical pytest-cuke parser setting.

  Scenario: Python selection executes a scenario from the pure-Python distribution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, then


      @given("the parser selection scenario starts", target_fixture="parser_selection_started")
      def parser_selection_starts():
          return True


      @then("the selected parser scenario completes")
      def parser_selection_completes(parser_selection_started):
          assert parser_selection_started is True
      """
    And consumer file "features/parser-selection.feature" contains:
      """gherkin
      Feature: Parser selection
        Scenario: Python parser selection
          Given the parser selection scenario starts
          Then the selected parser scenario completes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=python --cuke-summary"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: Automatic selection falls back when native support is unavailable
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/parser-selection.feature" contains:
      """gherkin
      Feature: Parser selection
        Scenario: Automatic parser fallback
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=auto --cuke-summary"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And pytest output should contain "falling back to Python"

  Scenario: Explicit Go selection explains how to install or build missing native support
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/parser-selection.feature" contains:
      """gherkin
      Feature: Parser selection
        Scenario: Explicit Go parser selection
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=go --cuke-summary"
    Then pytest should exit with a non-zero code
    And pytest output should contain "Go parser"
    And pytest output should contain "install"
    And pytest output should contain "build"

  Scenario: Command-line parser selection overrides the canonical configuration value
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_summary = true
      cuke_parser = "go"
      """
    And consumer file "features/parser-selection.feature" contains:
      """gherkin
      Feature: Parser selection
        Scenario: Command-line Python selection
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=python"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: Canonical cuke parser configuration selects Python without a command-line override
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_summary = true
      cuke_parser = "python"
      """
    And consumer file "features/parser-selection.feature" contains:
      """gherkin
      Feature: Parser selection
        Scenario: Configured Python parser
      """
    When I run installed pytest with arguments "--rootdir=."
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios

  Scenario: An unknown parser selection warns and behaves like automatic selection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/parser-selection.feature" contains:
      """gherkin
      Feature: Parser selection
        Scenario: Unknown parser fallback
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=not-a-parser --cuke-summary"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And pytest output should contain "unknown"
    And pytest output should contain "auto"

  Scenario: Malformed Gherkin remains a location-aware parse failure under automatic selection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/malformed.feature" contains:
      """gherkin
      Feature: Malformed parser input
        Scenario: Missing a valid step keyword
          Given a valid first step
          Invalid syntax without keyword
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=auto --cuke-summary"
    Then pytest should exit with a non-zero code
    And pytest output should contain "malformed.feature"
    And pytest output should contain "parse"

  # Conditional installed-package acceptance: CI can provide an actual host-built wheel.
  # The consumer installs and executes it; no mocked native loader can satisfy this scenario.
  Scenario: A supplied native wheel parses and executes through installed pytest autoload
    Given a host-built native pytest-cuke wheel is installed when supplied
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, then


      @given("the native parser scenario starts", target_fixture="started")
      def native_parser_starts():
          return True


      @then("the native parser scenario completes")
      def native_parser_completes(started):
          assert started is True
      """
    And consumer file "features/native.feature" contains:
      """gherkin
      Feature: Native parser consumer
        Background:
          Given the native parser scenario starts

        Rule: A native parser can collect real Gherkin scenarios
          Scenario: The installed native package executes a scenario
            Then the native parser scenario completes
      """
    When I run the native parser model parity test in the installed consumer
    Then the installed native wheel preserves the Python Feature model
    When I run installed pytest with arguments "--rootdir=. --cuke-parser=go --cuke-summary"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
