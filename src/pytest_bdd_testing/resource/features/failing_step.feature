Feature: failing step probe
  Scenario: failing step emits exception payloads
    Given a passing precondition
    When an exploding step executes
    Then this step is not reached
