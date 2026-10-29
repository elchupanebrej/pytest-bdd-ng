Feature: Tolerant step failures
  Scenario: Ignored tolerant step lets later steps run
    When an audited operation fails
    Then the workflow continues
