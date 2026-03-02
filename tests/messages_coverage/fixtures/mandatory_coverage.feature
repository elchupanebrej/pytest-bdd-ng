# comment for gherkinDocument.comments.text coverage
@feature_tag
Feature: Mandatory coverage feature
  Feature description line for coverage.

  Background: Base context
    Given a background value "from background"
    And a background table:
      | key   | value |
      | alpha | one   |

  @rule_tag
  Rule: Rule level validation

    Background: Rule background context
      Given a rule background value "rule background"

    @scenario_tag
    Scenario Outline: Rule scenario outline
      Given a number <number>
      When I attach textual and binary evidence for "<name>"
      Then result should be "<result>"

      Examples: Rule examples
        | number | name    | result |
        | 1      | sample1 | pass   |
        | 2      | sample2 | pass   |

  @top_scenario_tag
  Scenario: Top level scenario with doc string and table
    Given a background value "top-level"
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
