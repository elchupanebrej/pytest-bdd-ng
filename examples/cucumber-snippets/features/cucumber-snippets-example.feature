@snippets-example
Feature: Cucumber snippets example
  The real formatter suggests JavaScript bindings and preserves undefined steps.

  Background:
    Given the snippets example is ready

  Scenario: Suggestions retain a quoted Given parameter
    Given a customer named "Zoë" is registered

  Scenario: Suggestions retain a numeric When parameter
    When the customer waits 42 seconds

  Scenario: Suggestions retain a numeric Then parameter
    Then the customer receives 3 results
