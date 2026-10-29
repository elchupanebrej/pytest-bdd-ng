@public-json
Feature: Cucumber JSON example
  A checked-in project that demonstrates the public autoload contract.

  Background: Shared setup
    Given the Cucumber JSON example prepares a request

  Rule: Result serialization
    Background: Rule setup
      Given the Cucumber JSON example resets its output

    @report
    Scenario: A report includes structured inputs and an attachment
      Given the Cucumber JSON example receives a document
        """application/json
        {"message": "hello", "ready": true}
        """
      And the Cucumber JSON example receives a table
        | field | value |
        | café  | alpha |
      When the Cucumber JSON example processes the request
      Then the Cucumber JSON example response is "hello"
      And the Cucumber JSON example attaches a report

    Scenario Outline: An example row is recorded
      Given the Cucumber JSON example records "<label>"

      Examples:
        | label |
        | alpha |
        | bravo |
