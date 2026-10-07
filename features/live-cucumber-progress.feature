Feature: Live Cucumber progress formatter
  The selected progress formatter reports one Cucumber status marker per
  completed scenario attempt and summarizes outcomes from the Messages stream.

  Scenario: Quiet progress preserves pass, fail, skip, and undefined outcomes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a progress feature with passing, failed, skipped, and undefined scenarios
    And the consumer installs the pinned official Cucumber progress formatter packages
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress --cuke-messages-ndjson=progress.ndjson -q --tb=no --color=no"
    Then pytest should exit with a non-zero code
    And Cucumber progress markers should match every completed scenario attempt in "progress.ndjson"
    And the final Cucumber progress summary should report the four scenario outcomes

  Scenario: Retry progress markers remain correlated with their Messages attempts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer prepares a retryable progress scenario and installs pytest-rerunfailures
    And the consumer installs the pinned official Cucumber progress formatter packages
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-progress --cuke-messages-ndjson=retry.ndjson --reruns=1 -q --tb=no --color=no"
    Then pytest should exit with code 0
    And retry progress markers should correlate with distinct TestCaseStarted IDs in "retry.ndjson"
