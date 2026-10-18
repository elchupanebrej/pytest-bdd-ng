Feature: Live Cucumber formatter bridge
  Independently selected formatter plugins receive validated Messages as pytest
  runs and publish their output only after a clean shutdown.

  Scenario: The official Cucumber PrettyPrinter renders a live installed-consumer scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs the pinned Cucumber pretty formatter packages
    And the consumer registers the official PrettyPrinter as a live formatter
    And consumer file "features/official-pretty-formatter.feature" contains:
      """gherkin
      Feature: Official pretty formatter consumer
        Scenario: The official Cucumber formatter renders this scenario live
          Given the official formatter has rendered its scenario title
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And consumer artifact "pretty-output.txt" should contain the official Cucumber formatter output

  Scenario: A selected third-party formatter receives scenario messages live
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers live formatter plugin "probe" writing "probe.ndjson"
    And consumer file "features/live-formatter-bridge.feature" contains:
      """gherkin
      Feature: Live formatter consumer
        Scenario: The formatter observes this scenario while it runs
          Given the selected formatter has received the scenario start
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And consumer formatter artifact "probe.ndjson" should be one valid successful Messages stream

  Scenario: Independent formatter plugins receive identical ordered streams
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers independent formatter plugins "zeta" and "alpha"
    And consumer file "features/independent-formatters.feature" contains:
      """gherkin
      Feature: Independent live formatters
        Scenario: Both formatters observe a live scenario
          Given every selected formatter has received the scenario start
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And consumer formatter artifacts "alpha.ndjson" and "zeta.ndjson" should be identical valid successful Messages streams

  Scenario: A live formatter receives one normalized stream from xdist workers
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has pytest-xdist available or skips this scenario
    And the consumer registers live formatter plugin "xdist" writing "xdist-live.ndjson"
    And consumer file "features/xdist-live-formatter.feature" contains:
      """gherkin
      Feature: Live formatter with xdist workers
        Scenario: The northern worker scenario reaches the bridge
          Given formatter worker scenario north reaches the bridge

        Scenario: The southern worker scenario reaches the bridge
          Given formatter worker scenario south reaches the bridge
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --color=no -n 2 --dist=load --max-worker-restart=0 -q"
    Then pytest should exit with code 0
    And consumer formatter artifact "xdist-live.ndjson" should be one normalized stream for two xdist scenarios
    And consumer artifact "xdist-worker-batches.jsonl" should preserve contiguous callback sequences per worker

  Scenario Outline: Invalid output destinations fail before a scenario starts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers formatter destination case "<destination_case>"
    And consumer file "features/destination-conflict.feature" contains:
      """gherkin
      Feature: Formatter destination conflict
        Scenario: A conflicting formatter request must stop before execution
          Given the formatter scenario records that it started
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then the formatter destination conflict should be rejected before the scenario starts

    Examples:
      | destination_case |
      | duplicate        |
      | missing-parent   |
      | multiple-terminal|

  Scenario: Missing optional Node tooling is ignored when its formatter is unselected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers an optional formatter that requires Node and "@cucumber/pretty-formatter" when selected
    And consumer file "features/no-optional-formatter.feature" contains:
      """gherkin
      Feature: No optional formatter selected
        Scenario: The normal autoload run does not need formatter tooling
          Given the formatter scenario records that it started
      """
    And the installed consumer has no Node or "@cucumber/pretty-formatter" package available
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And the formatter scenario should have started without creating "optional.ndjson"

  Scenario: A failing selected formatter is reported without publishing a partial artifact
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers a formatter process that fails after receiving a message
    And consumer file "features/failing-formatter.feature" contains:
      """gherkin
      Feature: Failing live formatter
        Scenario: The selected formatter fails while consuming Messages
          Given the formatter scenario records that it started
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then the selected formatter failure should be visible and "broken.ndjson" should not be published

  Scenario: A failing formatter prevents sibling formatters from publishing partial artifacts
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers a healthy formatter alongside one that fails
    And consumer file "features/failing-formatter-sibling.feature" contains:
      """gherkin
      Feature: Failing formatter with a healthy sibling
        Scenario: No formatter may publish a partial shared run
          Given the formatter scenario records that it started
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then the formatter failure should prevent every selected output from being published

  Scenario: A formatter that exits on the first Messages envelope fails before scenario reporting
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers a formatter process that fails on its first Messages envelope
    And consumer file "features/first-envelope-failure.feature" contains:
      """gherkin
      Feature: First-envelope formatter failure
        Scenario: The formatter exits before scenario messages
          Given the formatter scenario records that it started
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then the first-envelope formatter failure should fail pytest and leave no "first-message.ndjson" output
