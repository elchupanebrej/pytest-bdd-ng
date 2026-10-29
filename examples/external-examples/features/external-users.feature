Feature: Users can be loaded from external examples
  Background:
    Given the user lookup service is ready

  Scenario Outline: The user record is looked up
    When I look up user <name> with tier <tier>
    Then the found user is <name> with tier <tier>

    Examples: table: users.csv
