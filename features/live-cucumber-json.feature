@e2e
Feature: Live message-driven Cucumber JSON formatter
  The default Cucumber JSON report is produced by the pinned official formatter
  from Messages, while the existing writer remains available by explicit choice.

  Scenario: CLI ini default path and independent reports use official JSON semantics
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JSON consumer prepares a rich feature in a Unicode workspace with spaces
    And the consumer installs the pinned official Cucumber JSON runtime
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json='artifacts/cli résumé.json' --cuke-summary --cuke-messages-ndjson=artifacts/messages.ndjson --junitxml=artifacts/junit.xml -q --color=no"
    Then the selected Cucumber JSON report should preserve the official feature scenario background outline tags doc string table attachments and durations
    And Cucumber JSON Messages JUnit and terminal summary should coexist as independent outputs
    When the Cucumber JSON consumer sets cuke_json to "artifacts/from-ini.json"
    And I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features -q --color=no"
    Then the configured Cucumber JSON report should preserve the official schema
    When the Cucumber JSON consumer removes cuke_json from configuration
    And I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json -q --color=no"
    Then the bare Cucumber JSON option should write the official report to "cucumber.json" under pytest root

  Scenario: Saved Messages replay after removing sources is semantically equivalent
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JSON consumer prepares a replay feature with source import and fixture traps
    And the consumer installs the pinned official Cucumber JSON runtime
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/live.json --cuke-messages-ndjson=messages.ndjson -q --color=no"
    Then the live Cucumber JSON report and Messages stream should be complete
    When I remove the Cucumber JSON consumer test sources and clear their execution markers
    And I run command "cuke" in the Cucumber JSON workspace with arguments "replay messages.ndjson --formatter cucumber-json=artifacts/replayed.json"
    Then replay should succeed without importing removed sources or running pytest fixtures
    And replayed Cucumber JSON should be semantically equivalent to the live report

  Scenario: Failure skip and undefined outcomes retain official statuses and diagnostics
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JSON consumer prepares passing failing skipped and undefined scenarios
    And the consumer installs the pinned official Cucumber JSON runtime
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/outcomes.json --cuke-messages-ndjson=artifacts/outcomes.ndjson -q --tb=short --color=no"
    Then the Cucumber JSON run should fail while publishing every outcome
    And the official report should preserve pass fail skip undefined status failure text and durations

  Scenario: Missing duplicate and unwritable destinations fail before scenarios run
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JSON consumer prepares a marker scenario for destination preflight
    And the consumer installs the pinned official Cucumber JSON runtime
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=missing-parent/report.json -q --color=no"
    Then the missing Cucumber JSON parent should fail before the marker scenario runs
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/../artifacts/shared.json --cuke-messages-ndjson=artifacts/shared.json -q --color=no"
    Then duplicate canonical Cucumber JSON destinations should fail before the marker scenario runs
    Given the Cucumber JSON output parent is read-only
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=read-only/report.json -q --color=no"
    Then the unwritable Cucumber JSON destination should fail before the marker scenario runs

  Scenario: An unselected JSON backend is inert and explicit native routing is preserved
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JSON consumer prepares a passing marker scenario
    And the Cucumber JSON consumer PATH excludes Node.js and npm
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features -q --color=no"
    Then ordinary pytest should pass without starting a JSON backend
    When the Cucumber JSON consumer clears the marker scenario result
    And I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/native.json --cuke-json-backend=native -q --color=no"
    Then the explicit native backend should preserve the legacy report and run without Node or npm

  Scenario: Selected runtime dependency and formatter finalization failures stay visible
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the Cucumber JSON consumer prepares a marker scenario for runtime preflight
    And the Cucumber JSON consumer PATH excludes Node.js and npm
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/report.json -q --color=no"
    Then missing Node diagnostics should stop the Cucumber JSON run before the marker scenario
    Given the Cucumber JSON consumer exposes Node.js without npm
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/report.json -q --color=no"
    Then missing npm diagnostics should stop the Cucumber JSON run before the marker scenario
    Given the Cucumber JSON consumer exposes Node.js and npm without installing Cucumber
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/report.json -q --color=no"
    Then missing Cucumber package diagnostics should stop the Cucumber JSON run before the marker scenario
    Given the consumer installs the pinned official Cucumber JSON runtime
    And the Cucumber JSON consumer installs a Node preload that fails during JSON finalization
    When I run installed pytest in the Cucumber JSON workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-json=artifacts/finalization.json -q --color=no"
    Then the Cucumber JSON backend failure should be visible and no partial report should be published
