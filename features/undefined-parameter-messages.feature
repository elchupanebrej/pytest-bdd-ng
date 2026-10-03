Feature: Undefined Cucumber parameters are reported accurately
  Unknown Cucumber-expression parameter types produce a schema-valid message,
  while ordinary mismatches, converter failures, and valid shared registrations
  retain their own outcomes.

  Scenario: Repeated matcher traversal emits one diagnostic per scenario attempt
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      import pytest
      from pytest_cuke import given, parsers


      @given(parsers.cucumber_expression("I use {unknownParameter}"))
      def use_unknown_parameter(unknownParameter):
          pass


      @pytest.hookimpl(hookwrapper=True)
      def pytest_runtest_makereport(item, call):
          outcome = yield
          report = outcome.get_result()
          if report.when != "call" or call.excinfo is None:
              return
          chain = []
          error = call.excinfo.value
          seen = set()
          while error is not None and id(error) not in seen:
              seen.add(id(error))
              chain.append({"type": type(error).__name__, "message": str(error)})
              error = error.__cause__ or error.__context__
          with Path("exception-chains.ndjson").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(chain))
              stream.write("\n")
      """
    And consumer file "features/unknown-parameters.feature" contains:
      """gherkin
      Feature: Unknown Cucumber parameter
        Scenario: The first unknown parameter use
          Given I use a sample value

        Scenario: A second scenario can report the same unknown parameter
          Given I use another value

        Scenario: An unrelated unmatched step is not an unknown parameter
          Given this unrelated phrase has no matching definition
      """
    When I run installed pytest in two independent sessions with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=first.ndjson --cuke-summary -q" and then "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=second.ndjson --cuke-summary -q"
    Then both message-reporting pytest sessions should fail with 3 BDD scenarios
    And consumer artifact "first.ndjson" should contain 2 schema-valid UndefinedParameterType messages with expression "I use {unknownParameter}" and name "unknownParameter"
    And consumer artifact "second.ndjson" should contain 2 schema-valid UndefinedParameterType messages with expression "I use {unknownParameter}" and name "unknownParameter"
    And consumer artifact "first.ndjson" should report 3 UNDEFINED steps, 3 failed scenarios, and an unsuccessful run
    And consumer artifact "second.ndjson" should report 3 UNDEFINED steps, 3 failed scenarios, and an unsuccessful run
    And consumer artifact "exception-chains.ndjson" should contain 6 exception chains and exactly 4 with UndefinedParameterTypeError
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "Step definition is not found"
    And pytest output should include "0 passed BDD scenarios, 3 failed, 0 skipped"
    And the consumer file "silent.ndjson" should not exist

  Scenario: Literal and regex mismatches and converter errors are not undefined types
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest import fixture
      from cucumber_expressions.parameter_type import ParameterType
      from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
      from pytest_cuke import given, parsers


      @fixture
      def parameter_type_registry():
          registry = ParameterTypeRegistry()

          def raise_for_value(value):
              raise ValueError("known parameter converter sentinel")

          registry.define_parameter_type(
              ParameterType(
                  name="failingCode",
                  regexp=r"\d+",
                  type=str,
                  transformer=raise_for_value,
              )
          )
          return registry


      @given("the registered literal step")
      def registered_literal_step():
          pass


      @given(parsers.re(r"^the registered regex step$"))
      def registered_regex_step():
          pass


      @given(parsers.cucumber_expression("I convert {failingCode}"), anonymous_group_names=["failingCode"])
      def convert_known_parameter(failingCode):
          pass
      """
    And consumer file "features/negative-controls.feature" contains:
      """gherkin
      Feature: Other failures are not undefined parameters
        Scenario: An unmatched literal definition
          Given this phrase has no literal definition

        Scenario: An unmatched regular expression definition
          Given this phrase has no regular expression match

        Scenario: A registered converter fails while transforming a known type
          Given I convert 42
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=negative.ndjson --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "0 passed BDD scenarios, 3 failed, 0 skipped"
    And pytest output should include "known parameter converter sentinel"
    And consumer artifact "negative.ndjson" should report one FAILED converter step and two UNDEFINED unmatched steps
    And consumer artifact "negative.ndjson" should contain no UndefinedParameterType messages

  Scenario: A shared custom parameter registry does not produce false diagnostics
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest import fixture
      from cucumber_expressions.parameter_type import ParameterType
      from pytest_cuke import given, parsers, then, when


      class Point:
          def __init__(self, x, y):
              self.x = int(x)
              self.y = int(y)

          def __eq__(self, other):
              return isinstance(other, Point) and (self.x, self.y) == (other.x, other.y)


      def parse_point(value):
          x, y = value.strip("()").split(",")
          return Point(x.strip(), y.strip())


      @fixture
      def parameter_type_registry(parameter_type_registry):
          parameter_type_registry.define_parameter_type(
              ParameterType(
                  name="point",
                  regexp=r"\(\d+,\s*\d+\)",
                  type=Point,
                  transformer=parse_point,
                  use_for_snippets=True,
                  prefer_for_regexp_match=True,
              )
          )
          return parameter_type_registry


      points = []


      @given(parsers.cucumber_expression("point {point} defined via cucumber expression"), anonymous_group_names=["point"])
      def given_point(point):
          assert point == Point(10, 20)
          points.append(point)


      @when(parsers.cucumber_regular_expression(r"point (?P<point>\(\d+,\s*\d+\)) defined via cucumber regex"))
      def when_point(point):
          assert point == Point(30, 40)
          points.append(point)


      @then("the shared points are recorded")
      def then_points_are_recorded():
          assert points == [Point(10, 20), Point(30, 40)]
      """
    And consumer file "features/shared-parameter-types.feature" contains:
      """gherkin
      Feature: Shared custom parameter types
        Scenario: A custom type is shared across expression parsers
          Given point (10, 20) defined via cucumber expression
          When point (30, 40) defined via cucumber regex
          Then the shared points are recorded
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=shared.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer artifact "shared.ndjson" should contain no UndefinedParameterType messages
