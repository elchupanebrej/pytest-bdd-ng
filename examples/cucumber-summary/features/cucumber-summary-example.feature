@summary-example
Feature: Cucumber Summary example
  The report counts each outline row and its executed steps.

  Background:
    Given the Summary example starts a clean ledger

  Scenario Outline: A summary counts each recorded entry
    When the Summary example records <entry>
    Then the Summary example confirms <entry>

    Examples:
      | entry |
      | alpha |
      | bravo |
