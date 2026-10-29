@e2e
Feature: StructBDD autoload discovery
  Installed consumers can discover supported structured BDD suffixes, ignore
  ordinary data files, select features through overlapping paths, and keep
  Gherkin collection useful when an optional structured loader is unavailable.

  Scenario: Autoload recognizes every supported suffix and ignores ordinary data files
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs pytest-cuke with its StructBDD extra
    And the consumer has one runnable feature for every supported StructBDD suffix
    And the consumer also has an uppercase StructBDD suffix variant
    When I compare StructBDD autoload by directory and by explicit files
    Then both StructBDD selections should collect all eight formats and the uppercase variant as passing scenarios
    And ordinary YAML and JSON data files and unsupported suffixes should be ignored

  Scenario: Overlapping directory and explicit file locators collect one scenario
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs pytest-cuke with its StructBDD extra
    And the consumer has one structured feature selected through overlapping locators
    When I run installed pytest with arguments "--rootdir=. -vv --color=no test_overlap.py"
    Then pytest should exit with code 0
    And the overlapping locators should collect the structured scenario once

  Scenario: StructBDD preserves equivalent Gherkin model and report output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs pytest-cuke with its StructBDD extra
    And the consumer has semantically equal Gherkin and YAML StructBDD features
    And pytest configuration:
      """toml
      [tool.pytest.ini_options]
      cuke_json_backend = "native"
      """
    When I compare their immutable feature models and scenario reports
    Then both formats should have matching normalized domains and Cucumber reports

  Scenario: Malformed data and a missing optional loader stay attributed while Gherkin runs
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs pytest-cuke with its StructBDD extra
    And the consumer has a core Gherkin feature, malformed structured data, and an optional JSON5 feature
    And the consumer blocks the optional JSON5 loader
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --continue-on-collection-errors -vv --color=no features"
    Then pytest should exit with a non-zero code
    And the StructBDD collection errors should identify both source files and the optional install extra
    And the core Gherkin scenario should still pass
