@e2e
Feature: Core pytest-cuke runs without optional Pydantic integrations
  Core pytest plugin loading and Cucumber Messages reporting do not require
  Pydantic. Pydantic-backed integrations remain available through their extras.

  Scenario: An installed core consumer runs BDD scenarios and writes Messages without Pydantic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/core.feature" contains:
      """gherkin
      Feature: Core consumer
        Scenario: Messages stay available
          Given the core pytest-cuke plugin loaded without optional Pydantic integrations
      """
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("the core pytest-cuke plugin loaded without optional Pydantic integrations")
      def core_plugin_loaded_without_pydantic():
          pass
      """
    And consumer file "test_core_runtime.py" contains:
      """python
      from importlib.util import find_spec
      from importlib.metadata import distribution


      def test_core_plugin_import_does_not_need_pydantic():
          assert find_spec("pydantic") is None
          import pytest_cuke.plugin
          import pytest_cuke.cli

          assert callable(pytest_cuke.plugin.pytest_addoption)
          assert callable(pytest_cuke.cli.main)


      def test_pydantic_is_declared_only_for_optional_integrations():
          requirements = distribution("pytest-cuke").requires or []
          pydantic_requirements = [
              requirement.lower() for requirement in requirements if "pydantic" in requirement.lower()
          ]

          assert pydantic_requirements
          assert all("extra ==" in requirement for requirement in pydantic_requirements)
          for extra in ("allure", "cucumber-json", "debug-mcp", "struct-bdd"):
              assert any("extra ==" in requirement and extra in requirement for requirement in pydantic_requirements)
      """
    Then the installed consumer should use the current PyPy 3.12 interpreter
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-parser=python --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer artifact "messages.ndjson" should be a valid Cucumber Messages stream for 1 passed scenario and 1 passed steps

  Scenario: A selected native Cucumber JSON backend explains its optional dependency
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=. --cuke-json-backend=native --cuke-json=report.json -q"
    Then pytest should exit with code 4
    And pytest output should contain "install pytest-cuke[cucumber-json]"

  Scenario: A selected Debug MCP integration explains its optional dependency
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=. --cuke-mcp-on-fail -q"
    Then pytest should exit with code 4
    And pytest output should contain "install pytest-cuke[debug-mcp]"

  Scenario: A structured feature explains its optional dependency
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "features/optional.bdd.yaml" contains:
      """yaml
      Feature: Optional structured feature
        Scenarios: []
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-parser=python -q"
    Then pytest should exit with a non-zero code
    And pytest output should contain "install pytest-cuke[struct-bdd]"

  Scenario: A selected native Allure integration explains its optional dependency
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    When I run installed pytest with arguments "--rootdir=. --cuke-features-dir=. --cuke-allure=allure-results -q"
    Then pytest should exit with code 4
    And pytest output should contain "install pytest-cuke[allure]"
