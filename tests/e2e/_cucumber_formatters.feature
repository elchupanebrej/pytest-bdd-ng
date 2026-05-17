Feature: cucumber formatter flags
  As a pytest-bdd-ng user
  I want to request cucumber-js formatter outputs from pytest
  So that I can reuse console and file reporters from the Cucumber ecosystem

  Scenario Outline: Render a console formatter from a command-line flag
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    When I run pytest with the console formatter flag "<flag>"
    Then pytest exits with test failures
    And stdout contains the user-visible line "<visible_output>"
    And stdout omits the default pytest terminal reporter output
    And the fake formatter stream source is "stdin"

    Examples:
      | flag                    | visible_output                           |
      | --cucumber-summary      | Summary: 2 scenarios (1 passed, 1 failed) |

  Scenario Outline: Render a file formatter from a command-line flag
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    When I run pytest with the file formatter flag "<flag>" writing to "<report_name>"
    Then pytest outcome must contain tests with statuses:
      | passed | failed |
      | 1      | 1      |
    And file "<report_name>" contains the rendered line "<visible_output>"
    And the fake formatter stream source is "stdin"

    Examples:
      | flag                   | report_name | visible_output |
      | --cucumber-json        | report.json | JSON formatter payload |
      | --cucumber-junit       | report.xml  | testsuite |
      | --cucumber-usage       | usage.txt   | Usage: Given a passing step x1; Given a failing step x1 |
      | --cucumber-usage-json  | usage.json  | "formatter": "usage-json" |

  Scenario: Render multiple formatter outputs in one run
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    When I run pytest with multiple cucumber formatter flags
    Then pytest exits with test failures
    And file "combined.json" contains the rendered line "JSON formatter payload"
    And file "usage.json" contains the rendered line "formatter"
    And the fake formatter stream source is "stdin"

  Scenario: Reject conflicting terminal formatter flags
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    When I run pytest with conflicting terminal formatter flags
    Then pytest exits with usage error
    And stderr contains the user-visible line "Only one terminal-output formatter may be active per run"

  Scenario: Reject file formatter output under a missing directory
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    When I run pytest with a file formatter pointing to a missing directory
    Then pytest exits with usage error
    And stderr contains the user-visible line "Formatter output directory does not exist"

  Scenario: Reject conflicting file formatter output paths
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    When I run pytest with conflicting file formatter output paths
    Then pytest exits with usage error
    And stderr contains the user-visible line "Multiple formatter outputs target the same path"

  Scenario: Render formatter outputs from an existing NDJSON report
    Given a fake node executable is available
    And a BDD suite with one passing and one failing scenario
    And a canonical messages NDJSON report generated at "messages.ndjson"
    When I run the standalone cucumber formatter renderer from that NDJSON
    Then the standalone renderer succeeds
    And standalone stdout contains the user-visible line "Summary: 2 scenarios (1 passed, 1 failed)"
    And file "standalone.json" contains the rendered line "JSON formatter payload"
    And file "standalone-usage.json" contains the rendered line "formatter"
    And the fake formatter stream source is "messagesPath"
