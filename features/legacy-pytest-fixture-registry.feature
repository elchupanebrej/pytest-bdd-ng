Feature: Pytest keeps parent fixture steps available in child projects

  Scenario: Child collection matches parent steps and uses its fixture override
    Given a pytester child has parent steps and a child fixture override
    When I run the pytester child in a subprocess
    Then the pytester child should pass its parent and override scenario
