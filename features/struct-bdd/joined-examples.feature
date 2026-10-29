Feature: StructBDD joined examples
  Joining example tables on shared parameters keeps only compatible rows.

  Scenario: Shared parameter values filter the Cartesian product
    Given StructBDD example tables share a parameter
    When the examples are joined
    Then only rows with matching shared parameter values remain
