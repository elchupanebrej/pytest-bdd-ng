Feature: Not-implemented step status policy
  Installed consumers select how explicitly marked not-implemented steps affect
  execution, fixtures, and reports. A not-implemented step never executes its
  body: the default error policy fails it, the explicit skip policy records a
  skip, and a local policy overrides the global setting.

  Scenario: The default error policy never runs a not-implemented body
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Default WIP policy
        Scenario: A not-implemented body fails by default
          When a not-implemented body raises "default WIP exception sentinel"
          Then a later step records "default-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed"
    And the consumer file "continuations.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "A not-implemented body fails by default" with step statuses "failed,skipped" and exception messages "Not-implemented step failed by policy: NotImplementedError." and run success "false"

  Scenario: The error policy never requests fixtures in either decorator order
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Strict WIP policy
        Scenario: Both decorator orders stop before injection and body
          When the first not-implemented parameter step requests fixture injection for "outer"
          And the second not-implemented parameter step requests fixture injection for "inner"
          Then a later step records "both-orders"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "Both decorator orders stop before injection and body" with step statuses "failed,skipped,skipped" and exception messages "Not-implemented step failed by policy: NotImplementedError." and run success "false"

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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with code 0
    And pytest output should include "1 skipped"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "A skipped not-implemented step does not request its fixture" with step statuses "skipped,skipped" and exception messages "" and run success "true"

  Scenario: The error policy fails a not-implemented body that would succeed
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Failed WIP policy
        Scenario: A not-implemented body never reports success
          When a not-implemented body succeeds
          Then a later step records "natural-success"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed"
    And the consumer file "continuations.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer artifacts "messages.ndjson" and "report.json" should agree for WIP scenario "A not-implemented body never reports success" with step statuses "failed,skipped" and exception messages "Not-implemented step failed by policy: NotImplementedError." and run success "false"

  Scenario: Local skip and error policies override the global policy
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP policy precedence
        @wip-status-skipped
        Scenario: A tag overrides the failed global policy
          When a not-implemented body raises "tag policy sentinel"
          Then a later step records "tag-policy"

        @wip-status-failed
        Scenario: A marker overrides its tag and the failed global policy
          When a not-implemented body raises "marker policy sentinel"
          Then a later step records "marker-policy"

        @wip-status-skipped
        Scenario: A marker overrides a skipped tag and the failed global policy
          When a not-implemented body raises "reverse marker policy sentinel"
          Then a later step records "reverse-marker-policy"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed, 2 skipped"
    And the consumer file "continuations.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A tag overrides the failed global policy" with step statuses "SKIPPED,SKIPPED" and exception messages ""
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A marker overrides its tag and the failed global policy" with step statuses "SKIPPED,SKIPPED" and exception messages ""
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A marker overrides a skipped tag and the failed global policy" with step statuses "FAILED,SKIPPED" and exception messages "Not-implemented step failed by policy: NotImplementedError."

  Scenario: An invalid local policy is a clear error
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Invalid local WIP policies
        @wip-status-unknown
        Scenario: An invalid tag is rejected
          When a not-implemented body raises "invalid tag sentinel"
          Then a later step records "invalid-tag-should-not-run"

        Scenario: An invalid marker is rejected
          When a not-implemented body raises "invalid marker sentinel"
          Then a later step records "invalid-marker-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "Invalid wip-status- policy"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist

  Scenario: Configuration supplies the WIP policy when the CLI is absent
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_wip_status = "skipped"
      """
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP configuration fallback
        Scenario: A configured skipped policy skips the body
          When a not-implemented body raises "configured policy sentinel"
          Then a later step records "configured-policy"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And pytest output should include "1 skipped"
    And the consumer file "continuations.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A configured skipped policy skips the body" with step statuses "SKIPPED,SKIPPED" and exception messages ""

  Scenario: The CLI policy overrides the configuration fallback
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_wip_status = "skipped"
      """
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP CLI override
        Scenario: CLI failed wins over the configured skip
          When a not-implemented body succeeds
          Then a later step records "cli-over-config"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "1 failed"
    And the consumer file "continuations.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "CLI failed wins over the configured skip" with step statuses "FAILED,SKIPPED" and exception messages "Not-implemented step failed by policy: NotImplementedError."

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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=unknown -q"
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "cuke_wip_status"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist

  Scenario: A skipped not-implemented setup does not invent its target fixture
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: WIP target fixture
        Scenario: A later step observes no target from a skipped setup
          When the not-implemented setup creates its target
          Then a later step records "target-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And pytest output should include "1 skipped"
    And the consumer file "continuations.log" should not exist
    And the consumer file "target-observation.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "messages.ndjson" should report WIP scenario "A later step observes no target from a skipped setup" with step statuses "SKIPPED,SKIPPED" and exception messages ""

  Scenario: Ordinary and undefined steps stay strict under the skipped policy
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
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=messages.ndjson -q"
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
        Scenario Outline: Not-implemented outline attempt <row>
          When a not-implemented outline step for "<row>" requests fixture injection
          Then a later step records "outline-<row>"

        Examples:
          | row   |
          | alpha |
          | beta  |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with code 0
    And pytest output should include "2 skipped"
    And the consumer file "continuations.log" should not exist
    And consumer artifact "messages.ndjson" should contain 2 coherent skipped WIP outline attempts matching "report.json"

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
    When I run installed pytest twice in one process with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-wip-status=skipped --cuke-messages-ndjson=skipped.ndjson -q" and then "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed --cuke-messages-ndjson=failed.ndjson -q"
    Then consumer repeated pytest sessions should exit with codes "0,1"
    And the consumer file "continuations.log" should not exist
    And the consumer file "wip-effects.log" should not exist
    And consumer Messages artifact "skipped.ndjson" should report WIP scenario "One WIP step follows each session policy" with step statuses "SKIPPED,SKIPPED" and exception messages ""
    And consumer Messages artifact "failed.ndjson" should report WIP scenario "One WIP step follows each session policy" with step statuses "FAILED,SKIPPED" and exception messages "Not-implemented step failed by policy: NotImplementedError."

  Scenario: Xdist workers isolate each WIP policy result
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And the installed consumer exposes not-implemented steps and policy probes
    And consumer file "features/wip-policy.feature" contains:
      """gherkin
      Feature: Isolated xdist WIP policies
        @wip-status-skipped
        Scenario: Each worker skips the skipped WIP scenario
          When the first not-implemented parameter step requests fixture injection for "xdist-skipped"
          Then a later step records "xdist-skipped"

        @wip-status-failed
        Scenario: Each worker stops the failed WIP scenario
          When a not-implemented body raises "xdist failed sentinel"
          Then a later step records "xdist-failed-should-not-run"
      """
    When I run installed pytest with arguments "--rootdir=. features --cuke-autoload --cuke-features-dir=features --cuke-wip-status=failed -n2 --dist=each -q"
    Then pytest should exit with a non-zero code
    And pytest output should include "2 failed, 2 skipped"
    And the consumer file "wip-effects.log" should not exist
    And the consumer file "continuations.log" should not exist
    And the consumer xdist WIP side-effect artifacts should not exist
