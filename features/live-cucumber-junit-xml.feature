@e2e
Feature: Live message-driven Cucumber JUnit XML formatter
  The official formatter consumes Cucumber Messages for pytest runs and replay.

  Scenario: CLI and ini selection publish structured official XML beside native JUnit
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares a rich feature with backgrounds and outline rows
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/cli.xml --cuke-messages-ndjson=artifacts/messages.ndjson --junitxml=artifacts/native.xml -q --color=no"
    Then the selected Cucumber JUnit report should preserve cases fields order and durations
    And Cucumber JUnit Messages native JUnit and pytest terminal summary should coexist
    When the Cucumber JUnit consumer sets cuke_junit to "artifacts/from-ini.xml"
    And I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features -q --color=no"
    Then the configured Cucumber JUnit report should preserve the same public contract
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit -q --color=no"
    Then the bare Cucumber JUnit option should write "cucumber.xml" under pytest root

  Scenario: Live and standalone replay produce equivalent normalized XML
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares a rich feature with backgrounds and outline rows
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/live.xml --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the selected Cucumber JUnit report should preserve cases fields order and durations
    When I replay Cucumber JUnit from the saved Messages stream to "artifacts/replayed.xml"
    Then replayed Cucumber JUnit XML should match live XML after normalizing timestamps

  Scenario: Passed failed skipped and undefined cases have truthful JUnit outcomes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares passing failing skipped and undefined scenarios
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/outcomes.xml --cuke-strict -q --tb=short --color=no"
    Then the Cucumber JUnit run should fail while publishing every case outcome

  Scenario: A failing Gherkin Background remains a failed case
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares a failing background scenario
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/background.xml -q --color=no"
    Then the Cucumber JUnit case should retain the failed background diagnostic

  Scenario: A failing scenario hook remains a failed case
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares a failing scenario hook
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/hook.xml -q --color=no"
    Then the Cucumber JUnit cases should retain failed before and after hook diagnostics

  Scenario: The original JUnit golden remains a deterministic Messages transport reference
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares passing and failing cases for the historical golden
    And the Cucumber JUnit consumer exposes its deterministic historical formatter
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/historical.xml -q --tb=short --color=no"
    Then the Cucumber JUnit report should match the historical reference golden

  Scenario: Missing and conflicting destinations fail before scenario execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares a marker scenario for destination preflight
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=missing-parent/report.xml -q --color=no"
    Then the missing Cucumber JUnit parent should fail before the marker scenario runs
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/shared.xml --junitxml=artifacts/../artifacts/shared.xml -q --color=no"
    Then duplicate canonical JUnit destinations should fail before the marker scenario runs
    Given the Cucumber JUnit consumer output parent is read-only
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=read-only/report.xml -q --color=no"
    Then the unwritable Cucumber JUnit destination should fail before the marker scenario runs

  Scenario: Missing formatter runtime and backend finalization failures stay visible
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JUnit consumer prepares a marker scenario for destination preflight
    And the Cucumber JUnit consumer PATH excludes Node.js and npm
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/report.xml -q --color=no"
    Then missing Cucumber JUnit runtime diagnostics should stop the run before the marker scenario
    Given the consumer installs the pinned official Cucumber JUnit runtime
    And the Cucumber JUnit consumer installs a Node preload that fails during XML finalization
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=artifacts/finalization.xml -q --color=no"
    Then the Cucumber JUnit backend failure should be visible without publishing a partial report

  Scenario: The public autoload example emits an inspectable JUnit report
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the public Cucumber JUnit example is copied to the installed consumer
    And the consumer installs the pinned official Cucumber JUnit runtime
    When I run installed pytest in the Cucumber JUnit workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-junit=report.xml -q --color=no"
    Then the public Cucumber JUnit example should match its pinned formatter golden and preserve its report contract
