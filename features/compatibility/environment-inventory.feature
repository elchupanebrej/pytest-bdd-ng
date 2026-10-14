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
    And CPython 3.12 Windows and macOS lanes should be required full-matrix cells

  Scenario: Required lanes agree with resolved tox and workflow selections
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then the environment inventory check should pass
    And its tox listing proof should match the real tox environment list
    And every required lane should have resolved command and CI selection proof
    And the active lane proof should record actual runtime Python pytest and platform versions
    And tox selector fragments should remain separate from configured environments

  Scenario: Tox base Python selectors match the canonical alternative runtime selectors
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then resolved tox base Python selectors should match inventory tox_base_python for PyPy and GraalPy

  Scenario: The matrix runner rejects runtime mismatches before launching tox
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    When the matrix runner checks a PyPy cell against a mismatched runtime version and platform
    Then it should reject the cell before invoking tox or writing evidence

  Scenario Outline: CPython 3.15 cells record runner identity before tox acceptance starts
    When I start CPython 3.15 cell "<cell_id>" with platform name "<platform_name>", platform "<platform>", machine "<machine>", and normalized architecture "<normalized_architecture>"
    Then its preflight evidence should record the expected interpreter and actual runner identity before tox starts

    Examples: CPython 3.15 operating systems
      | cell_id           | platform_name | platform     | machine | normalized_architecture |
      | cpython-315-linux   | linux  | Linux-test   | x86_64 | x86_64    |
      | cpython-315-macos   | darwin | Darwin-test  | arm64  | aarch64   |
      | cpython-315-windows | win32  | Windows-test | AMD64  | x86_64    |

  Scenario: The CPython 3.14 macOS runtime environment installs uv for consumer acceptance
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then the CPython 3.14 macOS tox config should include uv>=0.8

  Scenario: Active runtime policy and required cells match the current support contract
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then active runtime policy should require CPython 3.11 through 3.15 on Linux macOS and Windows
    And active runtime policy should require PyPy 3.12 and GraalPy 25.3 on Linux x86_64
    And GraalPy and CPython 3.15 cells should pin their setup-python inputs and expected interpreters
    And required CPython cells should use latest pytest 9 with the specified pytest 7 and 8 floor cells
    And every required runtime cell should include core install and example acceptance
    And optional extras should remain separate from required runtime acceptance
    And every required runtime cell should declare upstream availability installability product support required CI and measured evidence separately
    And every required cell should require measured Python pytest platform architecture SHA command selected and passed tests outcome and workflow URLs

  Scenario: The PyPy 3.12 Linux cell records exact measured acceptance evidence
    When I run the PyPy 3.12 Linux acceptance cell with measured evidence
    Then its measured evidence should record exact PyPy and pytest versions on Linux x86_64
    And its acceptance evidence should prove the core and executable example commands with SHA and CI links

  Scenario: PyPy 3.12 platform exclusions distinguish support evidence from upstream availability
    When I inspect the PyPy 3.12 platform exclusions
    Then macOS and Windows should remain upstream available and carry technical exclusion reasons

  Scenario: GraalPy evidence serialization preserves a measured Linux acceptance artifact and bundled pip
    When I serialize a previously measured GraalPy 25.3 Linux acceptance artifact
    Then serialized evidence should preserve exact GraalPy and pytest versions on Linux x86_64 and bundled pip
    And serialized acceptance evidence should preserve sdist installation core and tutorial results with exact CI links

  Scenario: GraalPy 25.3 platform exclusions distinguish support evidence from upstream availability
    When I inspect the GraalPy 25.3 platform exclusions
    Then macOS and Windows should remain upstream available and carry GraalPy-specific technical reasons

  Scenario: The first required Linux runtime cell is x86_64 in policy and CI
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then the CPython 3.11 Linux required cell should require x86_64 in runtime policy and CI

  Scenario: Historical rows and unsupported pairings remain reasoned without claiming active support
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    Then historical support rows should remain history and must not be active support
    And pytest 7 support should cover every Python pairing allowed by upstream constraints
    And each unsupported runtime or pytest pairing should have upstream evidence and a reason
    And every runtime exclusion should record upstream availability installability product support required CI measured evidence and a named reason
    And PyPy 3.10 and 3.11 exclusions should remain source-backed historical runtime records
    Then required lanes should include CPython 3.11 and 3.14
    And required lanes should exercise compatible pytest 7 8 and 9 versions
    And the older viable pytest minors should use compatible Python lanes
    And Python 3.9 and pytest versions below 7 should be explicitly unsupported and unselected

  Scenario: Runtime floors and canonical inventory keep core support evidence distinct
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then the project should require CPython 3.11 and pytest 7 or newer
    And CPython 3.10 and PyPy 3.11 should be explicit source-backed runtime exclusions
    And canonical runtime records should keep availability installability core support required CI result evidence and exclusion reason distinct
    And the first required runtime row should be Linux x86_64 CPython 3.11 with pytest 9 and complete evidence
    And optional integration outcomes should remain independent from core runtime support

  Scenario: Required runtime evidence links to the uploaded and aggregated CI artifact
    Given the repository environment inventory is copied to a temporary project
    When I change the canonical runtime artifact name
    Then the inventory check should reject the unlinked runtime artifact

  Scenario: Required runtime evidence artifact names match the aggregate download pattern
    Given the repository environment inventory is copied to a temporary project
    When I rename the runtime evidence artifact and its workflow upload outside the aggregate pattern
    Then the inventory check should reject the artifact excluded by the aggregate download

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

  Scenario: Optional package constraints reject installed versions outside declared requirements
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    When I probe an optional lane with installed packages outside declared version and PEP 508 requirements
    Then the inventory check should report each requested package constraint installed version and install remedy

  Scenario: Optional package requirements ignore missing packages with inactive PEP 508 markers
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    When I probe an optional lane with an absent package behind an inactive PEP 508 marker
    Then the inventory check should pass without a missing-package diagnostic for that package

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

  Scenario: Local uv evidence matches lanes that install uv for acceptance consumers
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then local uv evidence should match the tox acceptance environments that install uv

  Scenario: The messages schema tox environment uses the current Cucumber Messages fixture
    Then the messages schema tox command should use the fixture for the installed Cucumber Messages release
    And the messages schema inventory carrier should use the fixture for the installed Cucumber Messages release

  Scenario: Optional integration acceptance stays outside the required runtime matrix
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Given the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then optional integration cells should provide isolated optional acceptance
    And optional integration cells should declare their extra markers and package requirements
    And optional integration evidence should use its own aggregate group

  Scenario: StructBDD stays outside core runtimes and has isolated optional acceptance
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    Then required runtime tox environments should not install the StructBDD extra
    And the optional StructBDD integration cell should install and run its acceptance feature

  Scenario: The optional integration policy accepts the isolated StructBDD lane
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then the environment inventory check should pass
    And optional integration evidence should include the StructBDD environment

  Scenario: Debug MCP acceptance uses an isolated CPython lane
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And the repository environment inventory is loaded
    When I run the project environment inventory check in JSON mode
    Then the environment inventory check should pass
    And the optional Debug MCP integration cell should install and run its acceptance feature
    And optional integration evidence should include the Debug MCP environment
  Scenario: Installed metadata enforces the Python and pytest floors without PyPy-specific markers
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    Then installed package metadata should require Python 3.11 and pytest 7 without implementation-specific dependency markers

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
    And live formatter acceptance should emit per-scenario progress to workflow logs

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

  Scenario: Every full-matrix tox environment expands into its own canonical row
    Given the repository environment inventory is copied to a temporary project
    When I expand every full-matrix cell into tox environment rows
    Then every full-matrix tox environment should appear exactly once with canonical cell metadata

  Scenario: Optional integration environments expand into isolated evidence rows
    Given the repository environment inventory is copied to a temporary project
    When I expand every optional integration cell into tox environment rows
    Then every optional integration tox environment should appear exactly once with canonical cell metadata

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

  Scenario: Support guidance distinguishes pytest compatibility from measured CI coverage
    Given the contributor entry point and compatibility audit guide are loaded
    Then the guide should distinguish the broad pytest support promise from measured CI coverage
