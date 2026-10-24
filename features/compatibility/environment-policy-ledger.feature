@e2e
Feature: Historical environment policy ledger
  The repository keeps an independent, source-backed record of the runtime cells
  and concrete tox environments that existed at the pinned historical revision.

  Scenario: The live support ledger preserves the pinned historical matrix
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    And the pinned R support baseline is loaded
    When I run the project environment inventory check in JSON mode
    Then the environment inventory check should pass
    And the live support ledger should retain the pinned cells and classify retired cells with source-backed policy exclusions
    And historical incompatible tox environments should remain source-backed exclusions

  Scenario: The independent baseline detects a viable lane removed from inventory and tox
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    And the pinned R support baseline is loaded
    When I remove one viable historical lane from the isolated ledger inventory and tox config
    Then the independent historical baseline should report the missing lane ID and pinned source
