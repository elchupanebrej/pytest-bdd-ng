@usage-example
Feature: Cucumber Usage example
  The terminal report shows every discovered definition and its real matches.

  Background:
    Given the Usage example starts a clean request

  Scenario Outline: A report shows each matched example row
    When the Usage example handles <value>
    Then the Usage example records <value>

    Examples:
      | value |
      | alpha |
      | bravo |
