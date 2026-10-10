@e2e
Feature: Supported environment inventory and acceptance proof
  The repository owns one machine-readable inventory of supported test lanes.
  The compatibility command checks that tox and GitHub Actions select those lanes
  and reports real environment, command, and carrier evidence.

  Scenario: Required and excluded lanes carry explicit support evidence
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then each lane should declare runtime Python pytest platform capability and status
    And required lanes should declare tox environment workflow selector command prerequisites and carrier
    And unsupported lanes should have a source-backed reason and no active selector
    And CPython 3.12 Windows and macOS lanes should remain optional manual entries

  Scenario: Required lanes agree with resolved tox and workflow selections
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then the environment inventory check should pass
    And its tox listing proof should match the real tox environment list
    And every required lane should have resolved command and CI selection proof
    And the active lane proof should record actual runtime Python pytest and platform versions

  Scenario: The inventory preserves viable runtimes and pytest pairings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then required lanes should include CPython 3.14 and PyPy 3.11
    And required lanes should exercise compatible pytest 7 8 and 9 versions
    And the older viable pytest minors should use compatible Python lanes
    And Python 3.9 and pytest versions below 7 should be explicitly unsupported and unselected

  Scenario: The pre-commit environment resolves to the lint command
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then the pre-commit lane should resolve to a tox command that runs pre-commit
    And Ruff and typecheck lanes should resolve to their real tools

  Scenario: Optional capability lanes select real tests and fail closed on missing prerequisites
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then optional capability lanes should declare carriers without claiming runtime outcomes
    When I probe a declared optional capability lane
    Then its collect-only carrier probe should select tests without claiming runtime outcomes
    When I probe a temporary optional lane with a missing package prerequisite
    Then the inventory check should fail with the lane package and install remedy
    And the missing prerequisite should not be reported as a skip

  Scenario: Browser and remote lanes name runnable carriers and prerequisites
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then the inventory should include a Playwright browser lane with an HTML report carrier
    And the inventory should include socket via and SSH lanes with real report carriers
    And native and formatter lanes should name their test carriers and prerequisites

  Scenario: The doc-generation extra has a dedicated required lane
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Given the doc-generation package prerequisites are installed in the consumer
    When I run the project environment inventory check in JSON mode
    And I probe the required doc-generation lane
    Then the required doc-generation lane should select its pytest carrier
    And it should declare the doc-gen extra and Pandoc prerequisite
    And its tox environment and workflow selector should be active

  Scenario: An unresolved required lane fails with an actionable diagnostic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I check a temporary inventory with an unresolved tox workflow selector and command
    Then the inventory check should fail with a lane-specific tox workflow and command diagnostic

  Scenario: Every resolved tox environment has an inventory lane
    Given the repository environment inventory is copied to a temporary project
    When I check a temporary inventory omitting one resolved tox environment
    Then the inventory check should fail with a workflow lane and environment diagnostic

  Scenario: Workflow cells cannot select unresolved tox environments
    Given the repository environment inventory is copied to a temporary project
    When I add a nonexistent tox environment to a workflow cell
    Then the inventory check should fail with a workflow cell and environment diagnostic

  Scenario: Workflow jobs consume their matching matrix selection output
    Given the repository environment inventory is copied to a temporary project
    When I wire a workflow job to a different matrix selection output
    Then the inventory check should fail with a scoped matrix output diagnostic

  Scenario: Selector steps export the matrix output consumed by workflow jobs
    Given the repository environment inventory is copied to a temporary project
    When I remove the GitHub output flag from a selector step
    Then the inventory check should fail with a scoped matrix export diagnostic

  Scenario: Semantically overlapping optional and unsupported lanes are rejected
    Given the repository environment inventory is copied to a temporary project
    When I add an unsupported Windows lane overlapping the optional Windows lane
    Then the inventory check should fail with an actionable runtime lane conflict diagnostic
