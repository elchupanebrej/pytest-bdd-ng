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

  Scenario: CLI selection emits real JavaScript snippets with file output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares mixed undefined-step snippets in a Unicode workspace with spaces
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    When I run installed pytest from consumer directory "snippet workspace 東京 café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/report.json --cuke-usage-json=artifacts/cucumber-usage.json --junitxml=artifacts/junit.xml -q --color=no"
    Then the CLI selection should emit usable JavaScript snippets and preserve the undefined failure

  Scenario: Configuration selection emits real JavaScript snippets
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares mixed undefined-step snippets in a Unicode workspace with spaces
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    And the consumer enables cuke_snippets in its configuration
    When I run installed pytest from consumer directory "snippet workspace 東京 café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=artifacts/messages.ndjson -v --capture=tee-sys --color=no"
    Then the configuration selection should emit each JavaScript expression alternative once and preserve the undefined failure

  Scenario: A snippets formatter crash preserves pytest undefined-step failures
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares mixed undefined-step snippets in a Unicode workspace with spaces
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    And the consumer patches the pinned snippets formatter to fail after receiving the run messages
    When I run installed pytest from consumer directory "snippet workspace 東京 café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then the snippets backend failure should preserve pytest's undefined-step failures

  Scenario: Explicit capture modes preserve snippets and undefined-step failures
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares mixed undefined-step snippets in a Unicode workspace with spaces
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    When I run installed pytest from consumer directory "snippet workspace 東京 café" with shared arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets --color=no" and capture variants "-q --capture=fd", "-v --capture=sys", and "-vv --capture=no"
    Then fd capture should preserve JavaScript snippets and undefined-step failures while hiding passing step output
    And sys capture should preserve JavaScript snippets and undefined-step failures while hiding passing step output
    And disabled capture should preserve JavaScript snippets and undefined-step failures while showing passing step output

  Scenario: Duplicate canonical file destinations fail with snippets selected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a snippets backend preflight marker scenario
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets --cuke-json=artifacts/../artifacts/shared.json --cuke-messages-ndjson=artifacts/shared.json -q --color=no"
    Then duplicate snippets file destinations should fail before marker execution or artifact publication

  Scenario: The public snippets example emits real suggestions and keeps its undefined failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the public Cucumber snippets example is copied to the installed consumer
    And the consumer installs the pinned official Cucumber snippets runtime in that workspace
    When I run installed pytest from consumer directory "cucumber-snippets-example" with arguments "--cuke-parser=python --cuke-snippets -q --color=no"
    Then the public snippets example should emit JavaScript suggestions and preserve its undefined failure

  Scenario: Missing selected backend dependencies fail before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a snippets backend preflight marker scenario
    And Node.js and npm are available but the official Cucumber snippets package is absent
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then missing Cucumber snippets package preflight should be actionable and happen before execution
    Given the consumer exposes an isolated Node executable without npm
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then missing npm snippets preflight should be actionable and happen before execution
    Given Node.js and npm are unavailable to the consumer
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then missing Node.js snippets preflight should be actionable and happen before execution

  Scenario: A second terminal formatter is rejected before either formatter or scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a terminal formatter conflict marker scenario
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-snippets -q --color=no"
    Then the snippets terminal conflict should be rejected before formatter or scenario execution
