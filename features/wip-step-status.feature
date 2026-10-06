Feature: Not-implemented step status policy
  Installed consumers can select how explicitly marked not-implemented steps
  affect execution, fixtures, and reports.

  Scenario: The default failed policy runs a not-implemented body
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Default WIP policy
        Scenario: A not-implemented body fails by default
          When a not-implemented body raises "default WIP exception sentinel"
          Then a later step records "default-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "0 passed BDD scenarios, 1 failed, 0 skipped"
    And the consumer file "continuations.log" should not exist
    And consumer WIP side-effect artifact should list "before-step,before-call,body:raise"
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "A not-implemented body fails by default" with step statuses "failed,skipped" and exception messages "default WIP exception sentinel" and run success "false"

  Scenario: Passed policy bypasses injection and both decorator orders
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Passed WIP policy
        Scenario: Both decorator orders bypass injection and continue
          When the first not-implemented parameter step requests fixture injection for "outer"
          And the second not-implemented parameter step requests fixture injection for "inner"
          Then a later step records "both-orders"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=passed --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "both-orders"
    And the consumer file "wip-effects.log" should not exist
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "Both decorator orders bypass injection and continue" with step statuses "passed,passed,passed" and exception messages "" and run success "true"

  Scenario: Skipped policy bypasses injection and skips later steps
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Skipped WIP policy
        Scenario: A skipped not-implemented step does not request its fixture
          When the first not-implemented parameter step requests fixture injection for "skip"
          Then a later step records "skip-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json --cuke-summary -q"
    Then pytest should exit with code 0
    And pytest output should include "0 passed BDD scenarios, 0 failed, 1 skipped"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "A skipped not-implemented step does not request its fixture" with step statuses "skipped,skipped" and exception messages "" and run success "true"

  Scenario: Failed policy allows a naturally successful body to pass
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Failed WIP policy
        Scenario: A successful not-implemented body passes normally
          When a not-implemented body succeeds
          Then a later step records "natural-success"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "natural-success"
    And consumer WIP side-effect artifact should list "before-step,before-call,body:success"
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "A successful not-implemented body passes normally" with step statuses "passed,passed" and exception messages "" and run success "true"

  Scenario: Marker and tag policies override the global policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP policy precedence
        @WIP-STATUS-PASSED
        Scenario: A tag overrides the failed global policy
          When a not-implemented body raises "tag policy sentinel"
          Then a later step records "tag-policy"

        @wip-status-failed
        Scenario: A marker overrides its tag and the failed global policy
          When a not-implemented body raises "marker policy sentinel"
          Then a later step records "marker-policy"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer continuation artifact should list "tag-policy,marker-policy"
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A tag overrides the failed global policy" with step statuses "PASSED,PASSED" and exception messages ""
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A marker overrides its tag and the failed global policy" with step statuses "PASSED,PASSED" and exception messages ""

  Scenario: Invalid local policies fall through to a valid tag or global policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Invalid local WIP policies
        @wip-status-unknown
        Scenario: An invalid tag falls through to the passed global policy
          When a not-implemented body raises "invalid tag sentinel"
          Then a later step records "invalid-tag-fell-through"

        @wip-status-failed
        Scenario: An invalid marker falls through to the failed tag
          When a not-implemented body raises "invalid marker sentinel"
          Then a later step records "invalid-marker-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=passed --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 passed BDD scenarios, 1 failed, 0 skipped"
    And consumer continuation artifact should list "invalid-tag-fell-through"
    And consumer WIP side-effect artifact should list "before-step,before-call,body:raise"
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "An invalid tag falls through to the passed global policy" with step statuses "PASSED,PASSED" and exception messages ""
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "An invalid marker falls through to the failed tag" with step statuses "FAILED,SKIPPED" and exception messages "invalid marker sentinel"

  Scenario: Configuration supplies the WIP policy when the CLI is absent
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_wip_status = "passed"
      """
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP configuration fallback
        Scenario: A configured passed policy bypasses the body
          When a not-implemented body raises "configured policy sentinel"
          Then a later step records "configured-policy"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "configured-policy"
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A configured passed policy bypasses the body" with step statuses "PASSED,PASSED" and exception messages ""

  Scenario: The CLI policy overrides the configuration fallback
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_wip_status = "passed"
      """
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP CLI override
        Scenario: CLI failed runs a naturally successful body
          When a not-implemented body succeeds
          Then a later step records "cli-over-config"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    And consumer continuation artifact should list "cli-over-config"
    And consumer WIP side-effect artifact should list "before-step,before-call,body:success"
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "CLI failed runs a naturally successful body" with step statuses "PASSED,PASSED" and exception messages ""

  Scenario: Invalid CLI and configuration policies are rejected before step execution
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Invalid WIP global policy
        Scenario: The body would record accidental execution
          When a not-implemented body succeeds
          Then a later step records "invalid-policy"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=unknown --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "--cuke-wip-status"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist
    Given pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_wip_status = "unknown"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "cuke_wip_status"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist

  Scenario: A passed setup step does not invent its target fixture
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP target fixture
        Scenario: A later step observes the target of a bypassed setup
          When the not-implemented setup creates its target
          Then the later step confirms the WIP target is None
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=passed --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 1 passed scenarios
    And consumer continuation artifact should list "target-is-none"
    And the consumer file "target-observation.log" should exist
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A later step observes the target of a bypassed setup" with step statuses "PASSED,PASSED" and exception messages ""

  Scenario: Ordinary and undefined steps stay strict under passed policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Strict non-WIP steps
        Scenario: An ordinary body exception remains a failure
          When an ordinary operation raises under WIP policy
          Then a later step records "ordinary-should-not-run"

        Scenario: An undefined step remains undefined
          When this not-implemented operation has no step definition
          Then a later step records "undefined-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=passed --cuke-messages-ndjson=messages.ndjson --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "2 failed"
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "An ordinary body exception remains a failure" with step statuses "FAILED,SKIPPED" and exception messages "ordinary WIP exception sentinel"
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "An undefined step remains undefined" with step statuses "UNDEFINED,SKIPPED" and exception messages ""

  Scenario: Outline attempts close their Messages and JSON lifecycles
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP outline reporting
        @wip-status-passed
        Scenario Outline: Passed not-implemented outline attempt <row>
          When a not-implemented outline step for "<row>" requests fixture injection
          Then a later step records "outline-<row>"

        Examples:
          | row   |
          | alpha |
          | beta  |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json --cuke-summary -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer continuation artifact should list "outline-alpha,outline-beta"
    And consumer artifact "messages.ndjson" should contain 2 coherent passed WIP outline attempts matching "report.json"

  Scenario: WIP policy state is cleared between pytest sessions in one process
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Repeated WIP sessions
        Scenario: One WIP step follows each session policy
          When the first not-implemented parameter step requests fixture injection for "repeat"
          Then a later step records "repeat-session"
      """
    When I run installed pytest twice in one process with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=skipped.ndjson --cuke-summary -q" and then "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-wip-status=passed --cuke-messages-ndjson=passed.ndjson --cuke-summary -q"
    Then consumer repeated pytest sessions should exit with codes "0,0"
    And consumer continuation artifact should list "repeat-session"
    And consumer Messages artifact "skipped.ndjson" should report WIP scenario "One WIP step follows each session policy" with step statuses "SKIPPED,SKIPPED" and exception messages ""
    And consumer Messages artifact "passed.ndjson" should report WIP scenario "One WIP step follows each session policy" with step statuses "PASSED,PASSED" and exception messages ""

  Scenario: Xdist workers isolate each WIP policy result
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Isolated xdist WIP policies
        @wip-status-passed
        Scenario: Each worker continues the passed WIP scenario
          When the first not-implemented parameter step requests fixture injection for "xdist-passed"
          Then a later step records "xdist-passed"

        @wip-status-failed
        Scenario: Each worker stops the failed WIP scenario
          When a not-implemented body raises "xdist failed sentinel"
          Then a later step records "xdist-failed-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-wip-status=passed -n2 --dist=each --cuke-summary -q"
    Then pytest should exit with a non-zero code
    And consumer xdist continuation artifacts should show "xdist-passed" on 2 workers
    And consumer xdist WIP side-effect artifacts should show "before-step,before-call,body:raise" on 2 workers
