Feature: Tolerant step status policy
  A policy can ignore exceptions raised by explicitly tolerant step definitions,
  while Messages keeps the original failure and other pytest outcomes stay strict.

  Scenario: The default failed policy stops after a tolerant exception
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Default tolerant step policy
        Scenario: Default policy stops after the tolerant exception
          When the first tolerant operation raises an AssertionError
          Then the continuation records "default"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed"
    And the consumer file "continuations.log" should not exist
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,SKIPPED" and exception messages "first tolerant assertion sentinel" for scenario "Default policy stops after the tolerant exception" and TestRunFinished success "false"

  Scenario: The ignored CLI policy continues in either decorator order
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Ignored tolerant step policy
        Scenario: Both tolerant decorator orders continue
          When the first tolerant operation raises an AssertionError
          And the second tolerant operation raises a RuntimeError
          Then the continuation records "first-order,second-order"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=messages.ndjson --cuke-json=cucumber.json --cuke-progress -vv"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "first-order,second-order"
    And pytest output should include "When the first tolerant operation raises an AssertionError"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,FAILED,PASSED" and exception messages "first tolerant assertion sentinel,second tolerant runtime sentinel" for scenario "Both tolerant decorator orders continue" and TestRunFinished success "true"
    And consumer artifact "cucumber.json" should report scenario "Both tolerant decorator orders continue" with step statuses "failed,failed,passed" and error messages "first tolerant assertion sentinel,second tolerant runtime sentinel"

  Scenario: A pytest marker overrides its conflicting Gherkin tag and policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Tolerant policy precedence
        @tolerant-status-ignored
        Scenario: A Gherkin tag overrides the failed global policy
          When the first tolerant operation raises an AssertionError
          Then the continuation records "tag"

        @tolerant-status-failed
        Scenario: A pytest marker overrides the conflicting Gherkin tag
          When the first tolerant operation raises an AssertionError
          Then the continuation records "marker"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=failed --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer continuation artifact should list "tag,marker"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "first tolerant assertion sentinel" for scenario "A Gherkin tag overrides the failed global policy" and TestRunFinished success "true"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "first tolerant assertion sentinel" for scenario "A pytest marker overrides the conflicting Gherkin tag" and TestRunFinished success "true"

  Scenario: Invalid tag and marker policies fall through to the next valid policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Invalid local tolerant policies
        @tolerant-status-unknown
        Scenario: An invalid Gherkin tag falls through to the ignored global policy
          When the first tolerant operation raises an AssertionError
          Then the continuation records "invalid-tag"

        @tolerant-status-failed
        Scenario: An invalid pytest marker falls through to the failed Gherkin tag
          When the first tolerant operation raises an AssertionError
          Then the continuation records "invalid-marker"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 passed"
    And consumer continuation artifact should list "invalid-tag"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "first tolerant assertion sentinel" for scenario "An invalid Gherkin tag falls through to the ignored global policy" and TestRunFinished success "false"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,SKIPPED" and exception messages "first tolerant assertion sentinel" for scenario "An invalid pytest marker falls through to the failed Gherkin tag" and TestRunFinished success "false"

  Scenario: The CLI policy overrides the configuration fallback
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_tolerant_status = "ignored"
      """
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Global tolerant policy
        Scenario: A configured ignored policy continues by default
          When the first tolerant operation raises an AssertionError
          Then the continuation records "config"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=config.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "config"
    And consumer artifact "config.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "first tolerant assertion sentinel" for scenario "A configured ignored policy continues by default" and TestRunFinished success "true"
    When I remove consumer file "continuations.log"
    And I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=failed --cuke-messages-ndjson=cli-failed.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed"
    And the consumer file "continuations.log" should not exist
    And consumer artifact "cli-failed.ndjson" should keep tolerant step statuses "FAILED,SKIPPED" and exception messages "first tolerant assertion sentinel" for scenario "A configured ignored policy continues by default" and TestRunFinished success "false"

  Scenario: Skip and undefined outcomes stay strict under the ignored policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Strict non-exception outcomes
        Scenario: A tolerant skip remains skipped under ignored policy
          When a tolerant operation requests a skip
          Then the continuation records "skip"

        Scenario: An undefined operation remains undefined under ignored policy
          When this operation has no step definition
          Then the continuation records "undefined"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed, 1 skipped"
    And the consumer file "continuations.log" should not exist
    And consumer artifact "messages.ndjson" should retain skip and undefined statuses under the ignored policy

  Scenario: An undecorated step remains strict under the ignored policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Only decorated definitions are tolerant
        Scenario: An undecorated exception remains a failure
          When an ordinary operation raises a RuntimeError
          Then the continuation records "ordinary"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And the consumer file "continuations.log" should not exist
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,SKIPPED" and exception messages "ordinary runtime sentinel" for scenario "An undecorated exception remains a failure" and TestRunFinished success "false"

  Scenario: Fixture lookup errors remain strict under the ignored policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And the installed consumer exposes a tolerant step that requests a missing fixture
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Tolerant fixture lookup
        Scenario: A missing fixture is not supplied to a tolerant step
          When the tolerant operation requests a missing fixture
          Then the continuation records "missing-fixture-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=messages.ndjson --cuke-json=cucumber.json -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "fixture 'tolerant_missing_fixture' not found"
    And the consumer file "continuations.log" should not exist
    And the consumer file "missing-fixture-step-body.log" should not exist
    And consumer artifacts "messages.ndjson" and "cucumber.json" should report strict tolerant fixture lookup "tolerant_missing_fixture" for scenario "A missing fixture is not supplied to a tolerant step"

  Scenario: An ignored tolerant failure leaves a real target fixture available
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And the installed consumer declares a real target fixture for a failing tolerant step
    And consumer file "features/tolerant-target-fixture.feature" contains:
      """gherkin
      Feature: Tolerant target fixture
        Scenario: The later step consumes the real target fixture
          When the tolerant setup raises before returning its target fixture
          Then the later step consumes the real target fixture
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=messages.ndjson --cuke-json=cucumber.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "fixture-provided-target"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "tolerant target failure sentinel" for scenario "The later step consumes the real target fixture" and TestRunFinished success "true"
    And consumer artifact "cucumber.json" should report scenario "The later step consumes the real target fixture" with step statuses "failed,passed" and error messages "tolerant target failure sentinel"

  Scenario: An invalid CLI policy fails before executing a scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Invalid tolerant policy
        Scenario: The continuation would expose accidental execution
          Then the continuation records "invalid-cli"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=unknown -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "--cuke-tolerant-status"
    And the consumer file "continuations.log" should not exist

  Scenario: An invalid configuration policy fails before executing a scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_tolerant_status = "unknown"
      """
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Invalid tolerant policy
        Scenario: The continuation would expose accidental execution
          Then the continuation records "invalid-config"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "cuke_tolerant_status"
    And the consumer file "continuations.log" should not exist

  Scenario: Xdist workers resolve each scenario policy independently
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Isolated xdist tolerant policies
        @tolerant-status-ignored
        Scenario: Each worker continues the ignored scenario
          When the first tolerant operation raises an AssertionError
          Then the continuation records "worker-ignored"

        @tolerant-status-failed
        Scenario: Each worker stops the failed scenario
          When the first tolerant operation raises an AssertionError
          Then the continuation records "worker-failed"
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored -n2 --dist=each -q"
    Then pytest should exit with a non-zero code
    And consumer xdist continuation artifacts should show "worker-ignored" on 2 workers

  Scenario: Ambiguous tolerant definitions keep the first match and continue
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And the installed consumer exposes two duplicate tolerant step definitions
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Ambiguous tolerant bindings
        Scenario: The first matching definition runs and the next step continues
          When the ambiguous tolerant operation matches two definitions
          Then the continuation records "after-ambiguity"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And pytest output should include "Alternative step definitions are found"
    And consumer continuation artifact should list "first,after-ambiguity"

  Scenario: Consecutive pytest.main sessions resolve opposite tolerant policies independently
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes tolerant steps and a continuation artifact
    And consumer file "features/tolerant-status.feature" contains:
      """gherkin
      Feature: Tolerant policy across repeated sessions
        Scenario: The first session may continue the tolerant failure
          When the first tolerant operation raises an AssertionError
          Then the continuation records "repeat-session"
      """
    When I run installed pytest twice in one process with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=ignored --cuke-messages-ndjson=ignored.ndjson -q" and then "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-tolerant-status=failed --cuke-messages-ndjson=failed.ndjson -q"
    Then consumer repeated pytest sessions should exit with codes "0,1"
    And consumer artifact "ignored.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "first tolerant assertion sentinel" for scenario "The first session may continue the tolerant failure" and TestRunFinished success "true"
    And consumer artifact "failed.ndjson" should keep tolerant step statuses "FAILED,SKIPPED" and exception messages "first tolerant assertion sentinel" for scenario "The first session may continue the tolerant failure" and TestRunFinished success "false"
    And consumer continuation artifact should list "repeat-session"

  Scenario: The checked-in tolerant steps example runs from an installed consumer
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer stages the checked-in tolerant steps example
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=cucumber.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "continued"
    And consumer artifact "messages.ndjson" should keep tolerant step statuses "FAILED,PASSED" and exception messages "first tolerant assertion sentinel" for scenario "Ignored tolerant step lets later steps run" and TestRunFinished success "true"
    And consumer artifact "cucumber.json" should report scenario "Ignored tolerant step lets later steps run" with step statuses "failed,passed" and error messages "first tolerant assertion sentinel"
