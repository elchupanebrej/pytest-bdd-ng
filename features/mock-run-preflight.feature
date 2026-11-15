Feature: Mock-run binding preflight
  Binding validation before a run separates definitely missing step
  definitions from bindings that cannot be decided before earlier step bodies
  run, and reports not-implemented definitions without turning a mock run into
  an error or skip.

  Scenario: A definitely missing binding is reported as missing
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given


      @given("the bound preflight step records its execution")
      def bound_preflight_step_records_execution():
          Path("preflight-markers.txt").write_text("step-body", encoding="utf-8")
      """
    And consumer file "features/preflight-missing.feature" contains:
      """gherkin
      Feature: Preflight missing binding
        Scenario: The absent binding is reported
          Given the bound preflight step records its execution
          And the definitely absent preflight step is missing
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "the definitely absent preflight step is missing"
    And pytest output should include "Scenario has steps without matching step definitions:"
    And pytest output should not include "Scenario binding preflight is incomplete"
    And the consumer file "preflight-markers.txt" should not exist

  Scenario: A parser bound to a previous step target fixture is unverified, not missing
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import re
      from pathlib import Path

      from pytest_cuke import given, parsers, when


      def _record(name):
          with Path("preflight-markers.txt").open("a", encoding="utf-8") as stream:
              stream.write(name + "\n")


      class KnownNamesParser(parsers.StepParser):
          def __init__(self):
              self.regex = re.compile(r"^I select the name (?P<name>.+)$")

          def parse_arguments(self, request, name, anonymous_group_names=None):
              return self.regex.match(name).groupdict()

          @property
          def arguments(self):
              return ["name"]

          def is_matching(self, request, name):
              match = self.regex.match(name)
              if match is None:
                  return False
              known = request.getfixturevalue("known_names")
              return match.group("name") in (known or ())

          def __str__(self):
              return "I select the name %(name)s"


      @given("the known names are prepared", target_fixture="known_names")
      def known_names_are_prepared():
          _record("producer-body")
          return ["alpha"]


      @when(KnownNamesParser())
      def select_known_name(name):
          _record("dependent-body")
          assert name == "alpha"
      """
    And consumer file "features/preflight-dependent-parser.feature" contains:
      """gherkin
      Feature: Preflight dependent parser
        Scenario: The parser reads the target of the previous step
          Given the known names are prepared
          When I select the name alpha
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And the consumer file "preflight-markers.txt" should exist
    When I remove consumer file "preflight-markers.txt"
    And I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "Scenario binding preflight is incomplete"
    And pytest output should include "these step bindings are unverified"
    And pytest output should include "depends on fixture"
    And pytest output should include "known_names"
    And pytest output should include "produced by an earlier step"
    And pytest output should not include "without matching step definitions"
    And the consumer file "preflight-markers.txt" should not exist

  Scenario: A not-implemented definition is reported separately and mock run still succeeds
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given
      from pytest_cuke.steps import not_implemented


      @given("the scaffolded preflight step is pending")
      @not_implemented
      def scaffolded_preflight_step_is_pending():
          Path("preflight-markers.txt").write_text("step-body", encoding="utf-8")
      """
    And consumer file "features/preflight-not-implemented.feature" contains:
      """gherkin
      Feature: Preflight not-implemented definition
        Scenario: The scaffolded binding is found
          Given the scaffolded preflight step is pending
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run --cuke-wip-status=failed -q"
    Then pytest should exit with code 0
    And pytest output should include "Steps with @not_implemented definitions:"
    And pytest output should include "selected wip status policy: failed"
    And the consumer file "preflight-markers.txt" should not exist
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-mock-run --cuke-wip-status=skipped -q"
    Then pytest should exit with code 0
    And pytest output should include "selected wip status policy: skipped"
    And the consumer file "preflight-markers.txt" should not exist
