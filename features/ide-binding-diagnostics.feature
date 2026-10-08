Feature: IDE step binding diagnostics
  Installed consumers can resolve scenario and step source identities while
  Messages reports missing, ambiguous, and collection-time binding diagnostics.

  Scenario: Bind literal and parameterized steps to resolvable consumer sources
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer project root includes a Unicode character
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given, parsers, then, when


      _calls = []


      @given("the literal binding is selected")
      def literal_binding():
          _calls.append(("literal", None))


      @when(parsers.parse("I parse the name {name}"))
      def parse_name(name):
          _calls.append(("parse", name))


      @when(parsers.cfparse("I cfparse the name {name:w}"))
      def cfparse_name(name):
          _calls.append(("cfparse", name))


      @when(parsers.re(r"^I match the regex name (?P<name>[A-Za-z]+)$"))
      def regex_name(name):
          _calls.append(("regex", name))


      @when(parsers.cucumber_expression("I match the expression name {word}"), anonymous_group_names=["name"])
      def expression_name(name):
          _calls.append(("expression", name))


      @then("all five parser bindings ran")
      def all_parser_bindings_ran():
          assert _calls == [
              ("literal", None),
              ("parse", "Alice"),
              ("cfparse", "Bohdan"),
              ("regex", "Ira"),
              ("expression", "Olena"),
          ]


      def pytest_collection_finish(session):
          with Path("collected-nodeids.txt").open("a", encoding="utf-8") as artifact:
              artifact.write("\n".join(item.nodeid for item in session.items) + "\n")
      """
    And consumer file "features/parser-bindings.feature" contains:
      """gherkin
      Feature: Installed parser bindings
        Scenario: All parser forms keep their source identity
          Given the literal binding is selected
          When I parse the name Alice
          And I cfparse the name Bohdan
          And I match the regex name Ira
          And I match the expression name Olena
          Then all five parser bindings ran
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=relative.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer artifact "relative.ndjson" should report the five parser bindings with real source identities
    When I run installed pytest with an absolute consumer feature root and Messages file "absolute.ndjson"
    Then pytest should exit with code 0
    And consumer artifact "absolute.ndjson" should report the five parser bindings with real source identities

  Scenario: Missing and ambiguous steps are diagnosed without changing pytest outcomes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path

      import pytest
      from pytest_cuke import given, then


      _selected = []


      @given("the phrase that is available but not used")
      def available_but_unused():
          pass


      @given("the ambiguous operation is selected")
      def first_ambiguous_operation():
          _selected.append("first")


      @given("the ambiguous operation is selected")
      def second_ambiguous_operation():
          _selected.append("second")


      @then("the first ambiguous binding was selected")
      def first_binding_was_selected():
          assert _selected == ["first"]


      def pytest_collection_finish(session):
          with Path("collected-nodeids.txt").open("a", encoding="utf-8") as artifact:
              artifact.write("\n".join(item.nodeid for item in session.items) + "\n")


      @pytest.hookimpl(hookwrapper=True)
      def pytest_runtest_makereport(item, call):
          outcome = yield
          report = outcome.get_result()
          if report.when != "call" or call.excinfo is None:
              return
          with Path("failure-reports.ndjson").open("a", encoding="utf-8") as artifact:
              artifact.write(json.dumps({
                  "exceptionType": type(call.excinfo.value).__name__,
                  "message": str(call.excinfo.value),
              }) + "\n")
      """
    And consumer file "features/ambiguous-and-missing.feature" contains:
      """gherkin
      Feature: Ambiguous and missing source bindings
        Scenario: The first ambiguous definition still runs
          Given the ambiguous operation is selected
          Then the first ambiguous binding was selected

        Scenario: An unmatched step still fails naturally
          Given the unique missing phrase is needle-73
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=diagnostics.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 passed"
    And pytest output should include "Step definition is not found"
    And consumer artifact "diagnostics.ndjson" should report the missing step and both ambiguous candidates

  Scenario: Collection completion reports unbound and duplicate scenario bindings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      def pytest_collection_finish(session):
          with Path("collected-nodeids.txt").open("a", encoding="utf-8") as artifact:
              artifact.write("\n".join(item.nodeid for item in session.items) + "\n")
      """
    And consumer file "features/collection-bindings.feature" contains:
      """gherkin
      Feature: Collection-time scenario bindings
        Scenario: The source has multiple item bindings
          Given the explicitly bound scenario runs

        Scenario: This scenario has no pytest item binding
          Given the unbound scenario remains discoverable
      """
    And consumer file "test_duplicate_bindings.py" contains:
      """python
      from pytest_cuke import given, scenario


      @given("the explicitly bound scenario runs")
      def explicitly_bound_scenario_runs():
          pass


      @given("the unbound scenario remains discoverable")
      def unbound_scenario_remains_discoverable():
          pass


      @scenario("collection-bindings.feature", "The source has multiple item bindings")
      def test_first_collection_binding():
          pass


      @scenario("collection-bindings.feature", "The source has multiple item bindings")
      def test_second_collection_binding():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-messages-ndjson=collection.ndjson -q test_duplicate_bindings.py"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "collection.ndjson" should report unbound and duplicate scenario bindings with real node and case IDs

  Scenario: Duplicate bindings across loadfile workers keep every real case association
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import os
      from pathlib import Path

      def pytest_runtest_call(item):
          with Path("worker-nodeids.txt").open("a", encoding="utf-8") as artifact:
              artifact.write(f"{item.nodeid}\t{os.environ['PYTEST_XDIST_WORKER']}\n")
      """
    And consumer file "features/split-worker-bindings.feature" contains:
      """gherkin
      Feature: Split worker duplicate bindings
        Scenario: The shared source scenario has two bindings
          Given the shared worker scenario passes
      """
    And consumer file "tests/test_north_duplicate_binding.py" contains:
      """python
      from pytest_cuke import given, scenario


      @given("the shared worker scenario passes")
      def shared_worker_scenario_passes():
          pass


      @scenario("split-worker-bindings.feature", "The shared source scenario has two bindings")
      def test_north_shared_scenario_binding():
          pass
      """
    And consumer file "tests/test_south_duplicate_binding.py" contains:
      """python
      from pytest_cuke import given, scenario


      @given("the shared worker scenario passes")
      def shared_worker_scenario_passes():
          pass


      @scenario("split-worker-bindings.feature", "The shared source scenario has two bindings")
      def test_south_shared_scenario_binding():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-messages-ndjson=split-worker.ndjson -q -n2 --dist=loadfile tests"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "split-worker.ndjson" should contain one complete duplicate binding diagnostic for both worker modules

  Scenario: Outline rows keep separate sources across repeat sessions in one process
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer project root includes a Unicode character
    And consumer file "conftest.py" contains:
      """python
      from pathlib import Path

      from pytest_cuke import given, parsers


      @given(parsers.parse("the source row is {value:d}"))
      def source_row_is(value):
          assert value in {11, 22, 33, 44}


      def pytest_collection_finish(session):
          Path("collected-nodeids.txt").write_text(
              "\n".join(item.nodeid for item in session.items) + "\n",
              encoding="utf-8",
          )
      """
    And consumer file "features/outline-rows.feature" contains:
      """gherkin
      Feature: Outline row source identities
        Scenario Outline: The source row is <value>
          Given the source row is <value>

          @north-row
          Examples: North source line
            | value |
            | 11    |

          @south-row
          Examples: South source line
            | value |
            | 22    |
      """
    And consumer file "features/narrative/narrative-cafe.feature.md" contains:
      """markdown
      # Feature: Narrative café source

      ## Scenario: The narrative source has a Unicode title

      * Given the source row is 33
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=outline-first.ndjson -q"
    Then pytest should exit with code 0
    And consumer artifact "outline-first.ndjson" should report distinct source lines for both outline rows
    When I run installed pytest twice in one process with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=outline-second.ndjson -q" and then "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features/narrative --cuke-messages-ndjson=narrative-second.ndjson -q"
    Then consumer repeated pytest sessions should exit with codes "0,0"
    And consumer artifact "narrative-second.ndjson" should contain only the current narrative source identity

  Scenario: Xdist workers keep source metadata attached to their own feature items
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers


      @given(parsers.parse("the worker source is {value}"))
      def worker_source_is(value):
          assert value in {"north", "south"}
      """
    And consumer file "features/north-source.feature" contains:
      """gherkin
      Feature: North worker source
        Scenario: The north source is collected
          Given the worker source is north
      """
    And consumer file "features/south-source.feature" contains:
      """gherkin
      Feature: South worker source
        Scenario: The south source is collected
          Given the worker source is south
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=xdist.ndjson -n2 --dist=loadfile -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "xdist.ndjson" should keep both worker source identities separate
