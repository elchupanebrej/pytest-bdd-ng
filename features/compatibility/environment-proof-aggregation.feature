Feature: Aggregate the full supported environment proof
  The final proof includes every environment declared by the checked-in inventory.
  It fails when expected evidence is absent, empty, mislabeled, or tied to another SHA.

  Scenario: A complete proof reports all inventory environments and outcome groups
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And the proof summary should report serial parallel e2e external and quality groups
    And the proof summary should preserve actual evidence for every environment

  Scenario: The aggregator accepts an empty argument in a successful tox command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one successful tox test command contains an empty string argument
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment

  Scenario: The aggregator rejects a missing expected environment
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one expected environment is missing from the artifacts
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing environment diagnostic

  Scenario: The aggregator rejects a zero test selection
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one test-group environment records zero selected tests
    When I run the full environment proof aggregator
    Then the proof summary should fail with a selected no tests diagnostic

  Scenario: The aggregator rejects an absent test selection count
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one test-group environment omits its selected test count
    When I run the full environment proof aggregator
    Then the proof summary should fail with a selected no tests diagnostic

  Scenario: The aggregator rejects selected tests when none passed
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one test-group environment has selected tests but none passed
    When I run the full environment proof aggregator
    Then the proof summary should fail with a no tests passed diagnostic

  Scenario: The aggregator rejects duplicate evidence for an expected environment
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one expected environment artifact is duplicated
    When I run the full environment proof aggregator
    Then the proof summary should fail with a duplicate evidence diagnostic

  Scenario: The aggregator rejects an incorrect environment group
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment is assigned to the wrong proof group
    When I run the full environment proof aggregator
    Then the proof summary should fail with a group mismatch diagnostic

  Scenario: The aggregator rejects evidence for another commit SHA
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment records a different commit SHA
    When I run the full environment proof aggregator
    Then the proof summary should fail with a SHA mismatch diagnostic

  Scenario: The aggregator rejects an environment without its resolved command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment omits its resolved tox command
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing resolved command diagnostic

  Scenario: The aggregator rejects a test environment without its actual pytest version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one test-group environment omits its actual pytest version
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing actual pytest version diagnostic

  Scenario: The aggregator requires actual pytest for a latest quality tox factor
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And the quality environment py314-pytestlatest-mypy omits its actual pytest version
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing actual pytest version diagnostic

  Scenario: The aggregator rejects a pytest version that disagrees with its tox factor
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment records a pytest version that disagrees with its tox factor
    When I run the full environment proof aggregator
    Then the proof summary should fail with a pytest tox factor mismatch diagnostic

  Scenario: The aggregator rejects actual runtime Python and platform that disagree with inventory
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment records runtime Python and platform that disagree with inventory
    When I run the full environment proof aggregator
    Then the proof summary should fail with runtime Python and platform mismatch diagnostics

  Scenario: The aggregator rejects a parallel environment without pytest-xdist
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one parallel environment is missing its required pytest-xdist package
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing pytest-xdist diagnostic

  Scenario: The aggregator rejects an environment without its matching successful tox result entry
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment has no matching successful tox result entry
    When I run the full environment proof aggregator
    Then the proof summary should fail with a successful tox result entry diagnostic

  Scenario: The aggregator rejects a Playwright report missing tox-installed extras
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And the Playwright report environment is missing requested tox-installed extras
    When I run the full environment proof aggregator
    Then the proof summary should fail for missing Playwright report extras

  Scenario: The aggregator rejects a tox test result without its executed command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one tox test result has a zero return code but no command
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing tox result command
