@e2e
Feature: Structured BDD support requires its complete optional extra
  Unrelated Pydantic-backed integrations do not activate incomplete structured
  BDD support, while the dedicated extra provides every parser dependency.

  Scenario: The Allure extra does not enable structured feature parsing
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/optional.bdd.yaml" contains:
      """yaml
      Name: Optional structured feature
      Steps:
        - Step:
            Name: Structured scenario
      """
    And the consumer installs pytest-cuke with its Allure extra in an isolated environment
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-parser=python -q"
    Then pytest should exit with code 2
    And pytest output should contain "install pytest-cuke[struct-bdd]"

  Scenario: The complete StructBDD extra parses features and publishes Messages
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/optional.bdd.yaml" contains:
      """yaml
      Name: Optional structured feature
      Steps:
        - Step:
            Name: Structured scenario
            Steps:
              - Given: the full StructBDD extra parses structured features
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the full StructBDD extra parses structured features")
      def structured_feature_step():
          pass
      """
    And the consumer installs pytest-cuke with its StructBDD extra in an isolated environment
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-parser=python --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 1 passed steps
    And the structured YAML source is omitted from Cucumber Messages in artifact "messages.ndjson"
    And every Pickle step in artifact "messages.ndjson" refers to a Gherkin AST step
