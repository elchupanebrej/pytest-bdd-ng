# Feature: Allure Cucumber Converter CLI
  Verify the allure-cucumber CLI tool converts Cucumber Messages NDJSON files to Allure results.

## Scenario: Convert Cucumber Messages NDJSON to Allure results
  * Given File "test.feature.md" with content:

    ```gherkin
    # Feature: Simple pass
    ## Scenario: Pass scenario
    * Given a passing step
    ```
  * And File "conftest.py" with content:

    ```python
    from pytest_bdd import given
    @given("a passing step")
    def _pass():
        pass
    ```
  * And File "test_sample.py" with content:

    ```python
    from pytest_bdd import scenarios
    test = scenarios("test.feature.md", features_base_dir=".")
    ```
  * And run pytest

    | cli_args | test_sample.py | --messages-ndjson | messages.ndjson |
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli messages.ndjson --output allure-results`
  * Then the command exit code is 0
  * And directory "allure-results" must contain files matching "*-result.json"
  * And directory "allure-results" must contain files matching "*-container.json"

## Scenario: Handle missing NDJSON file gracefully
  * When run `python -m pytest_bdd.plugin.allure_formatter.cli nonexistent.ndjson`
  * Then the command exit code is 1
  * And the renderer terminal output includes:
    | Messages NDJSON file was not found |
