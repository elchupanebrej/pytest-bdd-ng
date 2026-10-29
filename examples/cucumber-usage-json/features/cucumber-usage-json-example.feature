@usage-json-example
Feature: Cucumber Usage JSON example
  The artifact keeps each used definition and the source match for every row.

  Background:
    Given the Usage JSON example starts a clean request

  Scenario Outline: A report records each example row
    When the Usage JSON example handles <value>
    Then the Usage JSON example records <value>

    Examples:
      | value |
      | alpha |
      | bravo |
