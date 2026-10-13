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
    And configured hook Python should match the pre-commit lane interpreter

  Scenario: The pre-commit lane installs typing extras and pins Ruff for the approved format scope
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then the pre-commit tox environment should install the testtypes and debug-mcp extras
    And Ruff pre-commit hooks should match the py314-ruff tox scope and pinned version
    And pre-commit text fixers should exclude upstream schemas and generated docs

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

  Scenario: Collection summaries count selected tests instead of the total
    When I parse a partially deselected pytest collection summary
    Then the selected count should be 2
    When I parse a fully deselected pytest collection summary
    Then the selected count should be 0

  Scenario: Browser and remote lanes name runnable carriers and prerequisites
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then the inventory should include a Playwright browser lane with an HTML report carrier
    And the inventory should include socket via and SSH lanes with real report carriers
    And native and formatter lanes should name their test carriers and prerequisites

  Scenario: The native parser tox environment provides uv for acceptance consumers
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then the native parser tox environment should install uv

  Scenario: The messages schema tox environment uses the current Cucumber Messages fixture
    Then the messages schema tox command should use the fixture for the installed Cucumber Messages release
    And the messages schema inventory carrier should use the fixture for the installed Cucumber Messages release

  Scenario: Installed metadata caps PyPy 3.10 dependencies without limiting other runtimes
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Then installed package metadata should cap dependencies for PyPy 3.10 and remain open for newer runtimes

  Scenario: Live formatter acceptance uses inventory selected lanes on every platform
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then live formatter acceptance should have resolved required lanes for Linux macOS and Windows
    And each live formatter acceptance lane should resolve to its selected CI cell and test carrier
    And the aggregate proof job should require and download live formatter acceptance evidence

  Scenario: Live formatter carrier probes match tox feature selection exactly
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then every live formatter acceptance carrier should select exactly the feature files selected by tox

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

  Scenario: Long full-matrix cells expand into canonical per-environment rows
    Given the repository environment inventory is copied to a temporary project
    When I expand the selected long full-matrix cells into tox environment rows
    Then each selected tox environment should appear exactly once with canonical cell metadata

  Scenario: Selector steps export the matrix output consumed by workflow jobs
    Given the repository environment inventory is copied to a temporary project
    When I remove the GitHub output flag from a selector step
    Then the inventory check should fail with a scoped matrix export diagnostic

  Scenario: Semantically overlapping optional and unsupported lanes are rejected
    Given the repository environment inventory is copied to a temporary project
    When I add an unsupported Windows lane overlapping the optional Windows lane
    Then the inventory check should fail with an actionable runtime lane conflict diagnostic

  Scenario: Contributors can find the full supported proof guidance
    Given the contributor entry point and compatibility audit guide are loaded
    Then the guide should expose the full-proof command artifact and prerequisites
    And the contributor entry point should link to the compatibility audit guide
