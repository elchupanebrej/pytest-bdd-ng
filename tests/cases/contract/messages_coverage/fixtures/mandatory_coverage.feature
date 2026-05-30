# dedicated runtime-evidence fixture for deep gherkinDocument branches and runtime reporter payloads
# feature-level comment to exercise gherkinDocument.comments.*
@feature_tag
Feature: Mandatory coverage feature
  Feature description line for coverage.
  Extra feature description line for coverage.

  Background: Base context
    Shared setup description for top-level background.
    Given a background value "from background"
    And a background doc string:
      """text/plain
      top background doc
      """
    And a background table:
      | key   | value |
      | alpha | one   |

  @top_scenario_tag
  Scenario: Top level scenario with doc string and table
    Top scenario description line for coverage.
    Given a background value "top-level"
    And a coordinate 10,20,30
    And a payload doc string:
      """json
      {
        "message": "hello"
      }
      """
    And a payload table:
      | left  | right |
      | one   | two   |
      | three | four  |
    When I attach textual and binary evidence for "top"
    Then result should be "pass"

  @top_outline_tag
  Scenario Outline: Top level scenario outline with examples
    Top outline description line for coverage.
    Given a number <number>
    Then result should be "<result>"

    @top_examples_tag
    Examples: Top examples
      Top examples description line for coverage.
      | number | result |
      | 3      | pass   |

  @rule_tag
  Rule: Rule level validation
    Rule description line for coverage.

    Background: Rule background context
      Shared setup description for rule background.
      Given a rule background value "rule background"
      And a rule background doc string:
        """text/plain
        rule background doc
        """
      And a rule background table:
        | key | value |
        | rb  | one   |

    @scenario_tag
    Scenario Outline: Rule scenario outline
      Rule scenario description line for coverage.
      Given a number <number>
      And a payload doc string:
        """json
        {
          "rule": "payload"
        }
        """
      And a payload table:
        | left  | right |
        | one   | two   |
      When I attach textual and binary evidence for "<name>"
      Then result should be "<result>"

      @rule_examples_tag
      Examples: Rule examples
        Rule examples description line for coverage.
        | number | name    | result |
        | 1      | sample1 | pass   |
        | 2      | sample2 | pass   |
