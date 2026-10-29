@e2e
Feature: PyPy 3.12 executes installed pytest-cuke scenarios
  The PyPy 3.12 lane runs a real installed consumer scenario with a pytest fixture
  and records a complete Cucumber Messages report.

  Scenario: A PyPy consumer runs a fixture-backed scenario and reports it
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest_cuke import given, parsers, then, when


      @pytest.fixture
      def starting_total():
          return 40


      @given("the fixture-backed starting total is available", target_fixture="total")
      def starting_total_is_available(starting_total):
          return starting_total


      @when(parsers.parse("I add {amount:d} to the total"), target_fixture="result")
      def add_to_total(total, amount):
          return total + amount


      @then(parsers.parse("the reported result is {expected:d}"))
      def reported_result_is(result, expected):
          assert result == expected
      """
    And consumer file "features/fixture-backed-scenario.feature" contains:
      """gherkin
      Feature: PyPy installed consumer
        Scenario: The installed runtime preserves pytest fixtures
          Given the fixture-backed starting total is available
          When I add 2 to the total
          Then the reported result is 42
      """
    Then the installed consumer should use the current PyPy 3.12 interpreter
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=features --cuke-autoload --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 3 passed steps
    And consumer Messages artifact "messages.ndjson" should identify scenario "The installed runtime preserves pytest fixtures"
