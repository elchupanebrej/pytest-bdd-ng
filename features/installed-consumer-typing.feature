Feature: Installed pytest-cuke typing contract
  Built distributions expose typed public facades that consumers can import,
  execute, and check without installing pytest-cuke optional extras.

  Scenario Outline: Wheel and sdist expose typed public facades in a base install
    Given the pytest-cuke <distribution> built from this checkout is installed in a fresh consumer project
    And consumer file "test_public_facades.py" contains:
      """python
      import importlib.metadata
      import importlib.util
      from pathlib import Path

      import pytest_cuke
      import pytest_cuke.parsers as parser_facade
      from pytest_cuke import given, parsers, scenario, scenarios, step, then, when


      def test_installed_public_facades_have_runtime_and_type_metadata():
          distribution = importlib.metadata.distribution("pytest-cuke")
          install_root = Path(distribution.locate_file("pytest_cuke")).resolve()
          assert Path(pytest_cuke.__file__).resolve().is_relative_to(install_root)
          assert set(pytest_cuke.__all__) == {
              "given",
              "when",
              "then",
              "step",
              "parsers",
              "scenario",
              "scenarios",
          }
          assert all(callable(value) for value in (given, when, then, step, scenario, scenarios))
          assert callable(parsers.parse)
          assert callable(parsers.re)
          assert parser_facade.parse("the number is {number:d}").arguments == ["number"]
          assert parser_facade.re(r"the number is (?P<number>\d+)").arguments == ["number"]
          assert importlib.util.find_spec("pytest_cuke") is not None
          assert importlib.util.find_spec("pytest_cuke.parsers") is not None
          assert all(
              importlib.util.find_spec(module) is None
              for module in (
                  "mypy",
                  "pyright",
                  "allure_pytest",
                  "allure_commons",
                  "hjson",
                  "json5",
                  "pyhocon",
                  "yaml",
                  "pytest_cuke_testing",
                  "pytest_cuke_test_support",
              )
          )
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers, then, when


      @given(parsers.parse("the installed number is {number:d}"), target_fixture="number")
      def installed_number_is(number: int) -> int:
          return number


      @when("I double the installed number", target_fixture="doubled")
      def double_installed_number(number: int) -> int:
          return number * 2


      @then(parsers.parse("the installed result is {expected:d}"))
      def installed_result_is(doubled: int, expected: int) -> None:
          assert doubled == expected
      """
    And consumer file "features/installed-facade.feature" contains:
      """gherkin
      Feature: Installed typed facades
        Scenario: A typed consumer binding runs from the installed distribution
          Given the installed number is 21
          When I double the installed number
          Then the installed result is 42
      """
    When I run installed pytest with arguments "--rootdir=. --color=no"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And the installed archive publishes type metadata for both public facades
    And the installed distribution archive excludes harness and test assets

    Examples:
      | distribution |
      | wheel        |
      | sdist        |

  Scenario Outline: Wheel and sdist provide types checked by pinned Mypy
    Given the pytest-cuke <distribution> built from this checkout is installed with pinned Mypy in a fresh consumer project
    And consumer file "typed_consumer.py" contains:
      """python
      from pytest_cuke import given, parsers, scenario, scenarios, step, then, when
      from pytest_cuke.parsers import StepParserProtocol, parse as ParseBuilder, re as RegexBuilder


      parse_expression: StepParserProtocol = ParseBuilder("the count is {count:d}")
      regex_expression: StepParserProtocol = RegexBuilder(r"I add (?P<amount>\d+)")


      @given(parse_expression, target_fixture="count")
      def count_is(count: int) -> int:
          return count


      @when(parsers.parse("I add {amount:d}"), target_fixture="total")
      def add_amount(count: int, amount: int) -> int:
          return count + amount


      @then(regex_expression)
      def total_is(total: int, amount: int) -> None:
          assert total == amount


      @step("the canonical facade is importable")
      def facade_is_importable() -> None:
          pass


      single_scenario = scenario("features/counting.feature")
      feature_scenarios = scenarios("features/counting.feature", filter_="count")
      """
    When I run pinned Mypy on consumer file "typed_consumer.py"
    Then pinned Mypy should accept the typed canonical facade example
    And consumer file "invalid_consumer.py" contains:
      """python
      from pytest_cuke import scenario


      invalid_scenario = scenario(42, "Items are counted")
      """
    When I run pinned Mypy on consumer file "invalid_consumer.py"
    Then pinned Mypy should reject the invalid scenario facade argument

    Examples:
      | distribution |
      | wheel        |
      | sdist        |
