@e2e
Feature: Live Cucumber Pretty formatter
  The optional Cucumber PrettyPrinter follows pytest selection, output, and
  lifecycle behavior while rendering a live installed-consumer run.

  Scenario: The official formatter renders source and all terminal outcomes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs the pinned official PrettyPrinter packages for live output
    And the consumer prepares a Unicode feature with a Background, two outline rows, a failure, and a skip
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-pretty -s -q --color=no"
    Then pytest should exit with a non-zero code
    And the live pretty output should preserve the feature source, Unicode, tables, and outcomes

  Scenario: Pretty output is visible before a later step finishes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs the pinned official PrettyPrinter packages for live output
    And the consumer prepares a feature with a deliberately gated later step
    When I release the gated step only after its scenario title appears in live pretty output
    Then the installed pytest run should finish after the live output gate is released

  Scenario: cuke_pretty works with Messages, JSON, JUnit, verbose, and tee-sys output from a Unicode path
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And a portable workspace café enables cuke_pretty and contains one Unicode feature
    And the consumer installs the pinned official PrettyPrinter packages in its portable workspace
    And the consumer installs the pinned official Cucumber JSON runtime in consumer directory "portable workspace café"
    When I run installed pytest from consumer directory "portable workspace café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/report.json --junitxml=artifacts/junit.xml --capture=tee-sys -v --color=no"
    Then pytest should exit with code 0
    And pretty, Messages, JSON, and JUnit outputs should coexist in the portable consumer workspace
    And verbose tee-sys output should retain its normal forwarding and capture behavior

  Scenario: Piped narrow output stays readable
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs the pinned official PrettyPrinter packages for live output
    And the piped pretty consumer has a Unicode scenario and a narrow terminal width
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-pretty -q --color=no"
    Then pytest should exit with code 0
    And the piped pretty output should contain readable Unicode and the scenario source

  Scenario: A real terminal receives readable pretty output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the terminal pretty consumer has a Unicode scenario
    And the consumer installs the pinned official PrettyPrinter packages for live output
    When I run installed pytest in a narrow terminal with pretty output enabled
    Then the narrow terminal pretty output should contain readable Unicode and the scenario source

  Scenario: Conflicting terminal formatters fail before the scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a scenario that records whether it started
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-pretty -q"
    Then the terminal formatter conflict should be rejected before the scenario starts

  Scenario: Missing optional Node tooling does not affect an unselected pretty formatter
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a normal feature without installing Node or Cucumber packages
    And Node is absent from the installed consumer PATH
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And the normal scenario should pass without creating pretty output

  Scenario: A selected PrettyPrinter with a missing npm package fails before the scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And Node and npm are available but the official PrettyPrinter package is unavailable to the consumer
    And the consumer prepares a scenario marker for pretty package preflight
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-pretty -q"
    Then missing PrettyPrinter package preflight should fail before the scenario starts

  Scenario: A selected PrettyPrinter with missing Node fails before the scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And Node is absent from the installed consumer PATH
    And the consumer prepares a scenario marker for pretty package preflight
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-pretty -q"
    Then missing Node preflight should fail before the scenario starts

  Scenario: A bounded fake PrettyPrinter runs through the installed public option
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a bounded fake PrettyPrinter package and a Unicode feature
    When I run installed pytest with the fake PrettyPrinter and a 20-second bound
    Then the fake pretty runtime should finish and report that it received live Messages

  Scenario: A PrettyPrinter process failure is reported after execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a PrettyPrinter backend that exits with an error after final Messages
    When I run installed pytest with the fake PrettyPrinter and a 20-second bound
    Then the pretty backend failure should be reported with the pytest run status
