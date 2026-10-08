@e2e
Feature: Cucumber undefined-step snippets
  The opt-in snippets formatter delegates suggestion generation to the official
  Cucumber runtime and preserves pytest's undefined-step failure.

  Scenario: Snippets stay inactive by default without Node or npm
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares an undefined-step snippets scenario with the default configuration
    And Node.js and npm are unavailable to the consumer
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q --color=no"
    Then the undefined-step failure should remain and no snippet backend should be requested

  Scenario: CLI and configuration selection emit real JavaScript snippets with file output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares mixed undefined-step snippets in a Unicode workspace with spaces
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    When I run installed pytest from consumer directory "snippet workspace 東京 café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the CLI selection should emit usable JavaScript snippets and preserve the undefined failure
    And the consumer enables cuke_snippets in its configuration
    When I run installed pytest from consumer directory "snippet workspace 東京 café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=artifacts/messages.ndjson -v --capture=tee-sys --color=no"
    Then the configuration selection should emit each JavaScript expression alternative once and preserve the undefined failure

  Scenario: Missing selected backend dependencies fail before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a snippets backend preflight marker scenario
    And Node.js and npm are available but the official Cucumber snippets package is absent
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then missing Cucumber snippets package preflight should be actionable and happen before execution
    Given Node.js and npm are unavailable to the consumer
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then missing Node.js snippets preflight should be actionable and happen before execution

  Scenario: A second terminal formatter is rejected before either formatter or scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a terminal formatter conflict marker scenario
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then the snippets terminal conflict should be rejected before formatter or scenario execution
