Feature: Run-aware lifecycle hooks
  The active run exposes the feature, scenario, current step, and previous step
  to installed consumer hook plugins.

  Scenario: First scenario starts without a previous step
    Given the first hook step records "first-start"
    When the next hook step records "first-middle"
    Then the final hook step records "first-end"

  Scenario: Second scenario also starts without a previous step
    Given the first hook step records "second-start"
    When the next hook step records "second-middle"
    Then the final hook step records "second-end"

  Scenario: Attachment hooks receive the active run
    Then the example attaches a report
