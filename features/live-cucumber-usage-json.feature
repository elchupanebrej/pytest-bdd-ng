@e2e
Feature: Live Cucumber Usage JSON formatter
  The selected file formatter preserves the official Usage JSON schema, real
  definition and match locations, and pytest outcomes.

  Scenario: CLI and ini selections write real Usage JSON for repeated outline and background matches
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares an outline and background feature in a Unicode workspace
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json='artifacts/usage résultat.json' -q --color=no"
    Then the Usage JSON artifact should preserve UTF-8 definitions matches and durations
    When the consumer adds an unused Usage JSON definition
    And I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json='artifacts/usage résultat.json' -q --color=no"
    Then the real Usage JSON artifact should include the unused definition without matches
    When the consumer selects Usage JSON through cuke_usage_json configuration
    And I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q --color=no"
    Then the configured Usage JSON path should contain the real schema

  Scenario: Failed skipped and undefined steps leave valid Usage JSON and preserve pytest status
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares passing failing skipped and undefined scenarios
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/outcomes.json --cuke-messages-ndjson=artifacts/messages.ndjson -q --tb=short --color=no"
    Then the Usage JSON artifact should retain matched steps across all outcomes and pytest should fail
    And the Messages artifact should report passed failed skipped and undefined outcomes

  Scenario: Usage JSON file coexists with Summary and independent file reports
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares two passing scenarios for combined reports
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json --cuke-summary --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/cucumber.json --junitxml=artifacts/junit.xml -q --color=no"
    Then Usage JSON Summary Messages Cucumber JSON and JUnit should be distinct valid outputs

  Scenario: Usage JSON file coexists with live Cucumber progress
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares two passing scenarios for combined reports
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json --cuke-progress --capture=tee-sys -q --color=no"
    Then Usage JSON and live progress should both report the two passing scenarios

  Scenario: Missing parents duplicate destinations and terminal conflicts fail before scenarios run
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares a marker scenario for preflight checks
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=missing-parent/usage.json -q --color=no"
    Then the missing Usage JSON parent should fail before the marker scenario runs
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/../artifacts/report.json --cuke-json=artifacts/report.json -q --color=no"
    Then duplicate canonical Usage JSON outputs should fail before the marker scenario runs
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json --cuke-summary --cuke-progress -q --color=no"
    Then competing terminal formatters should fail before the marker scenario runs
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json= -q --color=no"
    Then an empty Usage JSON path should fail before the marker scenario runs
    Given the Usage JSON output parent is read-only
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=read-only/usage.json -q --color=no"
    Then the unwritable Usage JSON destination should fail before the marker scenario runs

  Scenario: No selection leaves ordinary execution inactive without Node or npm
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares a passing marker scenario
    And the usage-json consumer PATH excludes Node.js and npm
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q --color=no"
    Then the normal scenario should pass without starting a Usage JSON backend

  Scenario: Selected Usage JSON reports missing Node npm and Cucumber package dependencies
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares a marker scenario for dependency checks
    And the usage-json consumer PATH excludes Node.js and npm
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json -q --color=no"
    Then missing Node diagnostics should stop the Usage JSON run before the marker scenario
    Given the usage-json consumer exposes Node.js without npm
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json -q --color=no"
    Then missing npm diagnostics should stop the Usage JSON run before the marker scenario
    Given the usage-json consumer restores Node.js and npm without installing Cucumber
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json -q --color=no"
    Then missing Cucumber package diagnostics should stop the Usage JSON run before the marker scenario

  Scenario: A resolved package entrypoint fails only after the scenario reaches the formatter sink
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares a passing marker scenario for package resolution
    And the usage-json consumer exposes a resolvable Cucumber package with a failing entrypoint
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json -q --color=no"
    Then the formatter sink failure should remain visible after scenario execution

  Scenario: Usage JSON backend finalization failures remain visible
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage-json consumer prepares a passing scenario for backend finalization
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    And the usage-json consumer installs a Node preload that fails during Usage JSON finalization
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json -q --color=no"
    Then the Usage JSON backend failure should remain visible

  Scenario: Checked-in autoload example matches the pinned Usage JSON semantic golden
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the public Cucumber Usage JSON example is copied to the installed consumer
    And the consumer installs the pinned official Cucumber Usage JSON runtime
    When I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the public Usage JSON example should preserve used and unused definitions
    And Usage JSON match durations should equal the emitted Messages durations
    When the consumer adds a new unused definition to the public Usage JSON example
    And I run installed pytest in the usage-json workspace with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-usage-json=artifacts/usage.json --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the newly added Usage JSON definition should appear without matches
    And Usage JSON match durations should equal the emitted Messages durations
    And the real pinned Usage JSON artifact should match the checked-in semantic golden
