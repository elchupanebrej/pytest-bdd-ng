@e2e
Feature: Live Cucumber Usage formatter
  The selected UsageFormatter reports the real definitions and matches collected
  by pytest-cuke, and respects terminal and file output selection.

  Scenario: CLI usage output maps repeated matches to real definition identities
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares six examples, repeated definition text, and a failing step
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage --cuke-messages-ndjson=artifacts/messages.ndjson -q --tb=short --color=no"
    Then the official usage table should match Messages definition identities and preserve pytest failure
    When the consumer adds an unused usage definition
    And I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage=- --cuke-messages-ndjson=artifacts/messages.ndjson -q --tb=short --color=no"
    Then the official usage output should add the unused definition as UNUSED

  Scenario: A Usage backend failure stays visible beside a failing scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares one failing scenario for backend finalization
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    And the usage consumer installs a Node preload that fails during UsageFormatter finalization
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the Usage backend failure should remain visible beside the pytest failure

  Scenario: The cuke_usage string configuration selects stdout output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a passing feature with cuke_usage configured as dash
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then configured usage should report the passing definition and its source

  Scenario: The cuke_usage configuration can select a report path
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a passing feature with a configured usage path
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then configured usage should write the report path without terminal output

  Scenario: Usage stays inactive by default without Node.js or npm
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a passing feature with default configuration
    And the usage consumer PATH excludes Node.js and npm
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q --color=no"
    Then the default run should pass without requesting the usage backend

  Scenario: A usage file coexists with JSON, JUnit, Messages, and a terminal formatter
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a Unicode workspace with spaces and a public terminal formatter
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage='artifacts/usage report.txt' --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/cucumber.json --junitxml=artifacts/junit.xml -q --color=no"
    Then the usage file and all independent report outputs should be valid

  Scenario: Bare and dash usage selections reject a competing stdout formatter before tests
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a terminal conflict scenario and a public terminal formatter
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage -q --color=no"
    Then a competing stdout formatter should be rejected before formatting or scenario execution
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage=- -q --color=no"
    Then a competing stdout formatter should be rejected before formatting or scenario execution

  Scenario: A missing usage output parent is rejected before tests or runtime lookup
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a preflight marker scenario
    And the usage consumer PATH excludes Node.js and npm
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage=missing-parent/usage.txt -q --color=no"
    Then the missing usage parent should fail before tests and before Node lookup

  Scenario: Canonically duplicate usage output is rejected before tests or runtime lookup
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a preflight marker scenario with a public file formatter
    And the usage consumer PATH excludes Node.js and npm
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage=artifacts/../artifacts/public-usage.json -q --color=no"
    Then the duplicate canonical usage destination should fail before tests or runtime lookup

  Scenario: An unwritable usage output parent is rejected before tests
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares an unwritable output parent and a marker scenario
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage=read-only/usage.txt -q --color=no"
    Then the unwritable usage destination should fail before scenario execution

  Scenario: Selecting usage reports missing Node.js, npm, and the Cucumber package
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a preflight marker scenario
    And the usage consumer PATH excludes Node.js and npm
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage -q --color=no"
    Then missing Node.js usage preflight should be actionable and happen before execution
    Given the usage consumer exposes an isolated Node executable without npm
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage -q --color=no"
    Then missing npm usage preflight should be actionable and happen before execution
    Given the usage consumer exposes Node.js and npm without installing the Cucumber package
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage -q --color=no"
    Then missing Cucumber package usage preflight should be actionable and happen before execution

  Scenario: Empty definitions use the official no-step-definitions message
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares an undefined feature without step definitions
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage -q --tb=short --color=no"
    Then the official usage formatter should report no step definitions and retain pytest failure

  Scenario: A narrow terminal keeps the usage table readable within its width
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the usage consumer prepares a short passing feature for terminal width checks
    And the consumer installs the pinned official Cucumber UsageFormatter runtime
    And the usage consumer sets the terminal width to 48 columns for the next pytest run
    When I run pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-usage -q --color=no"
    Then the narrow usage table should retain all columns and fit the terminal width
