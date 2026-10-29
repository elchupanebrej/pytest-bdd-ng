@public-junit
Feature: Cucumber JUnit example café
  This example records structured customer profiles in JUnit XML.

  Background: Shared report setup
    Given the Cucumber JUnit example prepares a profile

  @profile-rule
  Rule: Customer profiles
    Profiles keep their structured inputs available to the report.

    Background: Profile setup
      Given the Cucumber JUnit example confirms its profile setup

    @customer-profile
    Scenario Outline: Submit a profile for <customer>
      The report identifies the submitted customer.
      When the Cucumber JUnit example receives a profile document
        """application/json
        {"customer": "<customer>", "active": true}
        """
      And the Cucumber JUnit example receives profile fields
        | field    | value      |
        | customer | <customer> |
        | active   | true       |
      Then the Cucumber JUnit example accepts "<customer>"

      Examples: named profiles
        | customer |
        | Ada      |
        | Boris    |
