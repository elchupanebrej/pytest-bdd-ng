@e2e
Feature: Live Cucumber progress bar
  The opt-in progress bar reports completed Pickles through pytest's public CLI
  and configuration while preserving normal output and file reports.

  Scenario: Progress bar remains disabled without Node or npm unless selected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress-bar scenario that records execution
    And the consumer PATH has no Node.js or npm executables
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q --tb=no --color=no"
    Then pytest should exit with code 0
    And progress bar should remain disabled while the scenario runs

  Scenario: cuke_progress_bar enables readable piped progress with distinct file outputs
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares failing, skipped, and passing progress-bar scenarios in a Unicode workspace with spaces
    And the consumer registers a public usage formatter with a distinct output path
    And the consumer installs pinned official Cucumber progress formatter packages in that workspace
    When I run installed pytest from consumer directory "progress workspace café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/cucumber.json --cuke-usage-json=artifacts/cucumber-usage.json --junitxml=artifacts/pytest.xml -q --color=no"
    Then pytest should exit with a non-zero code
    And piped progress-bar markers should match completed Messages attempts in "artifacts/messages.ndjson"
    And progress-bar output should have no cursor controls and all distinct file reports should be valid

  Scenario: The public progress-bar example runs with the pinned formatter
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the public Cucumber progress-bar example is copied to the installed consumer
    And the consumer installs pinned official Cucumber progress formatter packages in that workspace
    When I run installed pytest from consumer directory "cucumber-progress-bar-example" with arguments "--rootdir=. --cuke-parser=python --cuke-progress-bar -q --color=no"
    Then the public progress-bar example should emit its markers and pass

  Scenario: Cucumber JSON and an extension cannot write to the same canonical destination
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress-bar scenario that records execution
    And the consumer registers a public formatter targeting a Cucumber JSON path alias
    And the consumer installs pinned official Cucumber progress formatter packages
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress-bar --cuke-json=artifacts/report.json -q --color=no"
    Then progress bar and Cucumber JSON destination collision should fail before the scenario starts

  Scenario: Core report sinks cannot share a destination
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress-bar scenario that records execution
    And the consumer creates the shared report output directory
    And the consumer PATH has no Node.js or npm executables
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress-bar --cuke-json=artifacts/shared.json --junitxml=artifacts/shared.json -q --color=no"
    Then duplicate core report destinations should fail before the scenario starts

  Scenario: A live backend failure preserves the ordinary scenario failure
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a failing scenario for progress-bar backend errors
    And the official progress formatter shim throws after receiving a test case
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress-bar -q --color=no"
    Then progress-bar backend failure should retain its error and the pytest scenario failure

  Scenario: Selecting the progress bar without its formatter package fails before execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress-bar scenario that records execution
    And Node and npm are available but the official progress formatter package is absent
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress-bar -q --color=no"
    Then missing progress-bar backend should fail before the scenario starts

  Scenario: Selecting the progress bar without Node fails before execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress-bar scenario that records execution
    And the consumer PATH has no Node.js or npm executables
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress-bar -q --color=no"
    Then missing Node progress-bar preflight should fail before the scenario starts

  Scenario: Progress bar conflicts with a second terminal formatter before execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress-bar scenario that records execution
    And the consumer installs pinned official Cucumber progress formatter packages
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress-bar --cuke-pretty -q --color=no"
    Then the progress-bar and pretty conflict should fail before the scenario starts

  Scenario: TTY progress updates each retry and completed Pickle within terminal width
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a retry, a skipped case, and a gated progress-bar scenario
    And a POSIX pseudo-terminal with 32 columns is available
    And the consumer installs pinned official Cucumber progress formatter packages
    And the consumer installs pytest-rerunfailures in the installed consumer
    When I run installed pytest in a 32-column terminal until the first live progress update
    Then the terminal progress updates should be live, width-aware, and capped at the unique Pickle total

  Scenario: Capture modes preserve live TTY progress and pytest output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a retry, a skipped case, and a gated progress-bar scenario
    And a POSIX pseudo-terminal with 32 columns is available
    And the consumer installs pinned official Cucumber progress formatter packages
    And the consumer installs pytest-rerunfailures in the installed consumer
    When I run installed pytest in a 32-column TTY with default capture and "-q", plus "--capture=fd -q", "--capture=sys -v", and "--capture=no -vv"
    Then TTY progress and pytest output should be restored for each capture mode
