Feature: Cached batch feature collection
  Pytest collects feature files once per collection session, chooses a collection
  strategy by the configured file-count threshold, and keeps failures attributable
  to the feature and external source that caused them.

  Scenario: Serial and spawn collection preserve the same scenarios without aiofiles
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And I create 3 simple consumer feature files
    And consumer file "features/external-batch.feature" contains:
      """gherkin
      Feature: External batch examples
        Scenario Outline: External row <name>

          Examples: table: external-batch.csv
      """
    And consumer file "features/external-batch.csv" contains:
      """csv
      name
      Ada
      Bao
      """
    When I compare serial and spawn collection of the installed consumer suite
    Then serial and spawn collection should have identical scenario identities, outcomes, and normalized messages

  Scenario: The command-line threshold overrides the configured threshold
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And I create 1 simple consumer feature file
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_batch_threshold = 2
      """
    And the consumer cannot start spawn workers
    When I compare collection with and without a command-line threshold override
    Then the command-line threshold should select parallel collection over configuration
    And both collection runs should pass every scenario

  Scenario: A configured threshold uses serial below the boundary and parallel at or above it
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_features_dir = "features"
      cuke_autoload = true
      cuke_batch_threshold = 3
      """
    And the consumer cannot start spawn workers
    When I compare collection at 2, 3, and 4 feature files
    Then collection should stay serial below the configured threshold and fall back at and above it
    And all three collection runs should pass every scenario

  Scenario: The platform default threshold is serial below its boundary and parallel at the boundary
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer cannot start spawn workers
    When I compare collection immediately below and at the platform default threshold
    Then the platform default threshold should be 50 on POSIX and 1000 elsewhere
    And collection should stay serial below the default and fall back at the default
    And both default-threshold collection runs should pass every scenario

  Scenario: A later pytest process sees an edited feature file
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/editable.feature" contains:
      """gherkin
      Feature: Editable source
        Scenario: The first version is collected
      """
    When I run independent collection processes before and after replacing "features/editable.feature" with:
      """gherkin
      Feature: Editable source
        Scenario: The updated version is collected
      """
    Then the later pytest process should collect the edited feature and pass its scenario

  Scenario: Equivalent feature paths do not duplicate items while distinct bindings remain
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/catalog.feature" contains:
      """gherkin
      Feature: Binding catalog
        Scenario: First requested scenario
        Scenario: Second requested scenario
      """
    And consumer file "test_bindings.py" contains:
      """python
      from pytest_cuke import scenario as bind_scenario, scenarios


      @scenarios(".", "../features", return_test_decorator=True)
      def test_feature_directories_are_normalized(scenario):
          assert scenario.name in {"First requested scenario", "Second requested scenario"}


      @bind_scenario("catalog.feature", "First requested scenario")
      def test_first_explicit_binding(scenario):
          assert scenario.name == "First requested scenario"


      @bind_scenario("catalog.feature", "Second requested scenario")
      def test_second_explicit_binding(scenario):
          assert scenario.name == "Second requested scenario"
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload"
    Then pytest should exit with code 0
    And the test outcome should have 4 passed scenarios

  Scenario: Malformed features and external source failures remain visible in batch collection
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/malformed.feature" contains:
      """gherkin
      Feature: Malformed batch input
        Scenario: Invalid step syntax
          Given a valid first step
          This line is not a Gherkin step
      """
    And consumer file "features/broken.csv" contains:
      """csv
      name,tier
      Ada
      """
    And consumer file "features/broken.feature" contains:
      """gherkin
      Feature: Broken batch source
        Scenario Outline: Read an invalid external table
          Given user <name> has tier <tier>

          Examples: table: broken.csv
      """
    And consumer directory "features/unreadable.csv" exists
    And consumer file "features/unreadable.feature" contains:
      """gherkin
      Feature: Unreadable batch source
        Scenario Outline: Read an unreadable external table
          Given user <name> has tier <tier>

          Examples: table: unreadable.csv
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-batch-threshold=1"
    Then pytest should exit with a non-zero code
    And pytest output should contain "malformed.feature"
    And pytest output should contain "parse"
    And pytest output should identify the feature and external source for each batch error
