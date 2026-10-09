@e2e
Feature: Live Cucumber Summary formatter
  The opt-in Cucumber SummaryFormatter reports finalized scenario and step
  outcomes while leaving independent report files available to the consumer.

  Scenario: Summary stays inactive by default without optional runtimes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a passing feature with the default configuration
    And the installed consumer PATH excludes Node.js and npm
    When I run installed pytest from consumer directory "summary default workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q --color=no"
    Then the normal consumer scenario should pass without starting the summary formatter

  Scenario: The CLI uses official SummaryFormatter output with file reports and API formatters
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a Background, two outline rows, a failure, and a skip with a public file formatter
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    When I run installed pytest from consumer directory "summary workspace café" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --cuke-messages-ndjson=artifacts/messages.ndjson --cuke-json=artifacts/report.json --cuke-usage-json=artifacts/cucumber-usage.json --junitxml=artifacts/junit.xml -q --color=no"
    Then the official Cucumber summary should report finalized scenario and step outcomes with duration
    And Messages, Cucumber JSON, JUnit XML, and the public FormatterRequest usage JSON should agree on four execution cases
    And the built-in Usage JSON should contain the used summary background definition
    And the official summary should appear on stdout and not stderr

  Scenario: The public Summary example runs with the official formatter
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the public Cucumber Summary example is copied to the installed consumer
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    When I run installed pytest from consumer directory "cucumber-summary-example" with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-summary -q --color=no"
    Then the public Summary example should pass with the official summary

  Scenario: Summary selection rejects duplicate canonical file destinations before execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a marker scenario for destination preflight
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    When I run installed pytest from consumer directory "summary destination conflict workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --cuke-json=artifacts/../artifacts/shared.json --cuke-messages-ndjson=artifacts/shared.json -q --color=no"
    Then duplicate summary file destinations should fail before the marker scenario runs

  Scenario: The cuke_summary setting works with verbose tee-sys output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a passing feature with cuke_summary enabled in configuration
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    When I run installed pytest from consumer directory "summary config workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -v --capture=tee-sys --color=no"
    Then the official Cucumber summary should report one passed scenario and one passed step with duration
    And verbose tee-sys output should forward the consumer step and the summary once

  Scenario: Summary rejects a competing terminal formatter before either one starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a terminal conflict marker scenario and a public terminal formatter
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    When I run installed pytest from consumer directory "summary conflict workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q --color=no"
    Then the competing terminal formatter should be rejected before formatting or scenario execution

  Scenario: A setup-time skip is included in the finalized summary
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares one setup-time skip and one passing scenario
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    When I run installed pytest from consumer directory "summary setup-skip workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the official Cucumber summary should count the setup-time skip and passing scenario

  Scenario: Selecting Summary without Node.js fails before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a dependency preflight marker scenario without runtime packages
    And the installed consumer PATH excludes Node.js and npm
    When I run installed pytest from consumer directory "summary dependency preflight workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q --color=no"
    Then the selected summary runtime failure should identify missing Node.js before execution

  Scenario: Selecting Summary without npm fails when Node.js is available
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a dependency preflight marker scenario without runtime packages
    And the installed consumer PATH exposes Node.js but excludes npm
    When I run installed pytest from consumer directory "summary dependency preflight workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q --color=no"
    Then the selected summary runtime failure should identify missing npm before execution

  Scenario: Selecting Summary without the Cucumber package fails before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a dependency preflight marker scenario without runtime packages
    And the consumer PATH exposes Node.js and npm without installing the Cucumber Summary package
    When I run installed pytest from consumer directory "summary dependency preflight workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q --color=no"
    Then the selected summary runtime failure should identify the missing Cucumber package before execution

  Scenario: Summary excludes a failed attempt that pytest reruns and passes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares a scenario that fails once and passes on retry
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    And the summary consumer installs pytest-rerunfailures
    When I run installed pytest from consumer directory "summary retry workspace" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --cuke-messages-ndjson=artifacts/messages.ndjson --reruns=1 -q --color=no"
    Then the official summary should count the final retry as passed and the earlier attempt as a warning
    And the Messages artifact should contain one test case with both retry attempts and their outcomes

  Scenario: A Summary backend finalization error stays visible without reporting success
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the summary consumer prepares one failing scenario for backend finalization
    And the consumer installs the pinned official Cucumber Summary runtime in its workspace
    And the summary consumer installs a Node preload that fails during SummaryFormatter finalization
    When I run installed pytest from consumer directory "summary-backend-error" with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary --cuke-messages-ndjson=artifacts/messages.ndjson -q --color=no"
    Then the Summary backend failure should be visible beside one failed scenario
    And the Messages artifact should retain one failed scenario and an unsuccessful test run
