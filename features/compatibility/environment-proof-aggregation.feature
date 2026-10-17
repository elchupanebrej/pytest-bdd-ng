@e2e
Feature: Aggregate the full supported environment proof
  The final proof includes every environment declared by the checked-in inventory.
  It fails when expected evidence is absent, empty, mislabeled, or tied to another SHA.

  Scenario: A complete proof reports all inventory environments and outcome groups
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And the proof summary should report serial parallel e2e external quality and optional groups
    And the proof summary should preserve actual evidence for every environment
    And the proof summary should preserve Linux Windows and macOS runner evidence

  Scenario: A complete proof preserves actual architecture and workflow links
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And the proof summary should preserve architecture and actual job and run links

  Scenario: Every environment records the host tox executable used by its run command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And host tox evidence should match each environment's resolved tox run command

  Scenario: Core CPython and GraalPy coverage evidence includes tox-local uv
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And core CPython and GraalPy coverage evidence should include tox-local uv

  Scenario: The aggregator rejects required runtime evidence without its architecture
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one required runtime environment omits its architecture
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing architecture diagnostic

  Scenario: The aggregator rejects required runtime evidence with an invalid architecture
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one required runtime environment reports an invalid architecture
    When I run the full environment proof aggregator
    Then the proof summary should fail with an invalid architecture diagnostic

  Scenario: The aggregator rejects required runtime evidence without its workflow job link
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one required runtime environment omits its workflow job link
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing workflow job link diagnostic

  Scenario: The aggregator rejects environment evidence without host tox version and command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment omits its host tox version and resolved command
    When I run the full environment proof aggregator
    Then the proof summary should fail for missing host tox evidence

  Scenario: The aggregator enforces an exact interpreter patch version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And CPython 3.15.0 reports a different patch version
    When I run the full environment proof aggregator
    Then the proof summary should fail with an exact interpreter version diagnostic

  Scenario: The aggregator rejects workflow links that identify different runs
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one environment records a job link from another workflow run
    When I run the full environment proof aggregator
    Then the proof summary should fail with a mismatched workflow run link diagnostic

  Scenario: GraalPy evidence accepts GraalVM as tox implementation identity
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And GraalPy tox results identify their implementation as GraalVM
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And the proof summary should retain the canonical GraalPy runtime evidence

  Scenario: Optional integration environments have a separate aggregate proof group
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And optional integration proof should be separated from core support groups

  Scenario: The optional Allure environment records Node and CLI evidence
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And the proof summary should preserve Node npm npx and Allure CLI evidence for optional Allure

  Scenario: The aggregator rejects optional Allure evidence without its Allure CLI version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And the optional Allure environment omits its Allure CLI version
    When I run the full environment proof aggregator
    Then the proof summary should fail for missing optional Allure CLI evidence

  Scenario: Live formatter acceptance outcomes appear in the aggregate proof
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And it should preserve passed live formatter acceptance outcomes for Linux macOS and Windows
    And it should preserve actual Node npm npx Allure CLI and tox-local uv evidence for live formatters

  Scenario: Browser report evidence preserves its external and tox-local system tools
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And it should preserve Node npm npx Allure CLI and tox-local uv evidence for browser reports

  Scenario: The aggregator rejects live formatter evidence without a required Node.js version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one live formatter environment omits its required Node.js version
    When I run the full environment proof aggregator
    Then the proof summary should fail for missing live formatter system tool versions

  Scenario: The aggregator rejects live formatter evidence without its tox-local uv version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one live formatter environment omits its required uv version
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing live formatter uv version diagnostic

  Scenario: The aggregator rejects live formatter evidence with uv outside its tox environment
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one live formatter environment records uv outside its tox environment
    When I run the full environment proof aggregator
    Then the proof summary should fail for a uv command outside its tox environment diagnostic

  Scenario: The aggregator rejects acceptance coverage evidence without tox-local uv proof
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And PyPy acceptance omits its tox-local uv version and xdist omits its uv command
    When I run the full environment proof aggregator
    Then the proof summary should fail with actionable acceptance uv diagnostics

  Scenario: The live formatter runner captures versions through Windows command shims
    When the live formatter runner captures required system tool versions
    Then it should record host tox Node npm npx Allure CLI and tox-local uv versions using resolved argv commands

  Scenario: Native parser proof preserves Go and compiler versions and commands on every platform
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And it should preserve Go and native compiler versions and commands for Linux macOS and Windows

  Scenario: The aggregator rejects native parser evidence without its Go version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one native parser environment omits its required Go version
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing Go version diagnostic

  Scenario: The aggregator rejects native parser evidence without its compiler version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one native parser environment omits its required compiler version
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing native compiler version diagnostic

  Scenario: The aggregator rejects native parser evidence without its Go version command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one native parser environment omits its resolved Go version command
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing Go version command diagnostic

  Scenario: The aggregator rejects native parser evidence without its compiler version command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one native parser environment omits its resolved compiler version command
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing native compiler version command diagnostic

  Scenario: The native parser runner records platform-specific compiler commands
    When the native parser runner captures toolchain evidence for Linux macOS and Windows
    Then it should record Go and native compiler versions and invocation commands

  Scenario: The matrix runner logs Unicode tox output under a cp1252 parent stdout
    Given PYTHONUTF8 is unset in the runner environment
    When I run the environment matrix runner with a non-ASCII evidence path and cp1252 parent stdout
    Then it should return tox status write evidence and escape unrepresentable log characters

  Scenario: The matrix runner records tox exit status 23 under cp1252 parent stdout
    Given PYTHONUTF8 is unset in the runner environment
    When I run the environment matrix runner with a non-ASCII evidence path and cp1252 parent stdout when tox exits 23
    Then it should return failure and record tox exit 23 in evidence

  Scenario: The matrix runner executes one selected tox environment with its canonical proof key
    When I run the matrix runner for one tox environment selected from its cell
    Then it should execute only that environment and record the canonical proof key and SHA

  Scenario: The matrix runner rejects an environment outside its selected cell
    When I run the matrix runner for a tox environment outside its cell
    Then it should reject the environment before invoking tox or writing evidence

  Scenario: The aggregator accepts complete and interrupted runtime evidence from every remote transport
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    When I run the full environment proof aggregator
    Then the proof summary should pass and include every inventory environment
    And the proof summary should preserve two-worker socket via and ssh runtime evidence

  Scenario: The aggregator rejects a remote environment without worker runtime evidence
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one remote environment omits actual worker runtime evidence
    When I run the full environment proof aggregator
    Then the proof summary should fail with a missing remote worker runtime diagnostic

  Scenario: The aggregator rejects a remote worker without its runtime versions
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one remote worker omits its runtime and Python versions
    When I run the full environment proof aggregator
    Then the proof summary should fail with missing remote worker version diagnostics

  Scenario: The aggregator rejects remote worker versions that disagree with the inventory
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one remote worker reports runtime and Python versions that disagree with the inventory
    When I run the full environment proof aggregator
    Then the proof summary should fail with mismatched remote worker version diagnostics

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

  Scenario: The aggregator rejects an optional xdist environment without pytest-xdist
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one optional xdist environment is missing its pytest-xdist package
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

  Scenario: The aggregator rejects a doc-generation lane missing its optional packages
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And the doc-generation environment is missing its recorded optional package versions
    When I run the full environment proof aggregator
    Then the proof summary should fail for missing doc-generation packages

  Scenario: The aggregator rejects doc-generation evidence without the Pandoc CLI version
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And the doc-generation environment omits its required Pandoc CLI version
    When I run the full environment proof aggregator
    Then the proof summary should fail for missing Pandoc CLI version evidence

  Scenario: The aggregator rejects a tox test result without its executed command
    Given evidence artifacts are synthesized from every job cell and tox environment in the inventory
    And one tox test result has a zero return code but no command
    When I run the full environment proof aggregator
    Then the proof summary should fail for a missing tox result command

  Scenario: A duplicate step warning from an xdist worker deserializes in the installed package
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer requires pytest-xdist
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the duplicate xdist warning step")
      def first_duplicate_xdist_warning_step():
          pass


      @given("the duplicate xdist warning step")
      def second_duplicate_xdist_warning_step():
          pass
      """
    And consumer file "features/duplicate-xdist-warning.feature" contains:
      """gherkin
      Feature: Duplicate xdist warning
        Scenario: The worker reports its duplicate step warning
          Given the duplicate xdist warning step
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -n2 --dist=load --max-worker-restart=0 --color=no -q"
    Then pytest output should show the duplicate step warning without an xdist internal error
