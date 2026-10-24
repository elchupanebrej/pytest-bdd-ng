Feature: Parse failures emit Cucumber ParseError messages
  Invalid source files remain pytest collection errors while reporting the source
  and one-based location through the installed consumer message stream.

  Scenario: Serial Gherkin collection writes one ParseError before aborting
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Broken Gherkin
        Scenario: Invalid step syntax
          Given a valid step
          Invalid syntax without keyword
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-batch-threshold=999 --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And consumer artifact "messages.ndjson" should contain exactly one valid ParseError for feature "features/broken.feature" at line 4 column 5

  Scenario: Explicit feature selection reports its parse failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Broken Gherkin
        Scenario: Invalid step syntax
          Given a valid step
          Invalid syntax without keyword
      """
    And consumer file "features/not-selected.feature" contains:
      """gherkin
      Feature: Unselected invalid Gherkin
        Scenario: This file is outside the explicit selection
          Given a valid step
          Invalid syntax without keyword
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-batch-threshold=999 --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q features/broken.feature"
    Then pytest should exit with a non-zero code
    And consumer artifact "messages.ndjson" should contain exactly one valid ParseError for feature "features/broken.feature" at line 4 column 5

  Scenario: Spawn worker collection preserves ParseError through collect-only abort
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Broken Gherkin
        Scenario: Invalid step syntax
          Given a valid step
          Invalid syntax without keyword
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-batch-threshold=1 --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --collect-only -q"
    Then pytest should exit with a non-zero code
    And consumer artifact "messages.ndjson" should contain exactly one valid ParseError for feature "features/broken.feature" at line 4 column 5

  Scenario: Markdown Gherkin reports the original source and a one-based EOF location
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/broken.feature.md" contains:
      """markdown
      # Feature: Unclosed Markdown
        ## Scenario: Unclosed doc string
        * Given a step
        ```
        unclosed docstring without closing fence
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-batch-threshold=999 --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And consumer artifact "messages.ndjson" should contain exactly one valid ParseError for feature "features/broken.feature.md" at line 6 column 1

  Scenario: Disabling message reporting leaves the normal collection diagnostic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Broken Gherkin
        Scenario: Invalid step syntax
          Given a valid step
          Invalid syntax without keyword
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-batch-threshold=999 --cuke-features-dir=features -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "FeatureConcreteParseError"
    And the consumer file "messages.ndjson" should not exist

  Scenario: A consumer message hook receives ParseError without explicit NDJSON output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import json
      from pathlib import Path
      from pytest_cuke.model.message_types import message_to_dict


      def pytest_cuke_message(config, message):
          with Path("hook-messages.ndjson").open("a", encoding="utf-8") as stream:
              stream.write(json.dumps(message_to_dict(message)))
              stream.write("\n")
      """
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Broken Gherkin
        Scenario: Invalid step syntax
          Given a valid step
          Invalid syntax without keyword
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-batch-threshold=999 --cuke-features-dir=features -q"
    Then pytest should exit with a non-zero code
    And consumer artifact "hook-messages.ndjson" should contain exactly one valid ParseError for feature "features/broken.feature" at line 4 column 5
    And the consumer file "messages.ndjson" should not exist
