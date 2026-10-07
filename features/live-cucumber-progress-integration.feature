Feature: Cucumber progress selection and terminal integration
  The opt-in progress formatter follows pytest configuration, streams case
  markers live, and can share a run with file formatters.

  Scenario: Progress is disabled by default when Node and npm are unavailable
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a default progress scenario
    And Node and npm are absent from the installed consumer PATH
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -v --tb=no --color=no"
    Then pytest should exit with code 0
    And progress should remain unselected by default

  Scenario: The cuke_progress ini option enables progress without a CLI flag
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares an ini-enabled progress scenario
    And the consumer installs pinned official Cucumber progress packages
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=progress.ndjson -q --color=no"
    Then pytest should exit with code 0
    And progress output should contain one passing marker from "progress.ndjson"
    And the Cucumber progress summary should include one passing scenario

  Scenario: Verbose tee-sys progress coexists with file formatters in a Unicode workspace
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares two passing scenarios in a Unicode workspace with spaces
    And the consumer installs pinned official Cucumber progress packages in that workspace
    When I run installed pytest from consumer directory "progress workspace café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/report.json --capture=tee-sys -v --color=no"
    Then pytest should exit with code 0
    And progress output should contain two passing markers from "artifacts/messages.ndjson"
    And Messages and JSON artifacts should be valid in the Unicode workspace
    And verbose tee-sys should forward the passing step output

  Scenario: Pretty and progress terminal formatters conflict before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress preflight marker scenario
    And the consumer installs pinned official Cucumber progress packages
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-pretty --cuke-progress -q --color=no"
    Then the pretty and progress conflict should fail before the scenario starts

  Scenario: Selecting progress without Node fails before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress preflight marker scenario
    And Node and npm are absent from the installed consumer PATH
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress -q --color=no"
    Then missing Node progress preflight should fail before the scenario starts

  Scenario: Selecting progress without its npm package fails before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress preflight marker scenario
    And Node and npm are available but the official progress package is absent
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress -q --color=no"
    Then missing progress package preflight should fail before the scenario starts

  Scenario: A skipped scenario marker arrives before a later scenario finishes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a skipped scenario followed by a gated progress scenario
    And the consumer installs pinned official Cucumber progress packages
    When I release the gated scenario only after its skipped progress marker appears
    Then the installed consumer should finish after the marker was observed early
