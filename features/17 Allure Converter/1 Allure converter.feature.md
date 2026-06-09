# Feature: Allure-Cucumber Converter
  This feature documents the Allure-Cucumber Converter's ability to convert
  Cucumber Messages NDJSON files to Allure3 JSON result files.

## Scenario: Convert a minimal valid NDJSON to Allure results
  Given a cucumber messages NDJSON file with one passing scenario
  When the allure-cucumber converter processes the file
  Then an Allure result JSON file is created
  And the result JSON validates against the Allure3 events schema
  And the result has status "passed"

## Scenario: Convert NDJSON with multiple scenarios
  Given a cucumber messages NDJSON file with two scenarios
  When the allure-cucumber converter processes the file
  Then two Allure result JSON files are created
  And a container JSON file references both results

## Scenario: Handle empty NDJSON gracefully
  Given an empty cucumber messages NDJSON file
  When the allure-cucumber converter processes the file
  Then no error occurs

## Scenario: CLI rejects nonexistent input file
  Given a nonexistent NDJSON file path
  When the allure-cucumber CLI is invoked with that path
  Then the CLI exits with a non-zero code

## Scenario: Runtime plugin generates Allure results during pytest run
  Given File "features/sample.feature" with content:

    ```gherkin
    Feature: Sample
      Scenario: Passing
        Given a passing step
    ```

  And File "conftest.py" with content:

    ```python
    from pytest_bdd import given

    @given("a passing step")
    def _():
      pass
    ```

  And File "test_sample.py" with content:

    ```python
    from pytest_bdd import scenarios

    test = scenarios("sample.feature")
    ```

  And File "allure-results/messages.ndjson" with Cucumber Messages content for one passing scenario

  When run pytest

    | cli_args | --allure-cucumber-output | allure-output | -k | test_sample.py |

  Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

  And Directory "allure-output" contains Allure result JSON files
  And Allure result files validate against the Allure3 events schema

  When run docker

    | image   | allure3-local:latest |
    | command | allure generate /allure-results -o /allure-report   |
    | volume  | allure-output:/allure-results:ro          |
    | volume  | allure-report:/allure-report                |

  Then Directory "allure-report" contains Allure HTML report with index.html
  And Allure HTML report contains scenario name "Passing"

## Scenario: Convert existing NDJSON file to Allure report via CLI
  Given File "existing-messages.ndjson" with Cucumber Messages content for one passing scenario

  When run `python -m pytest_bdd.plugin.allure_cucumber.cli existing-messages.ndjson --output allure-cli-output`

  Then Directory "allure-cli-output" contains Allure result JSON files
  And Directory "allure-cli-output" contains a container JSON file referencing the results

  When run docker

    | image   | allure3-local:latest |
    | command | allure generate /allure-results -o /allure-report   |
    | volume  | allure-cli-output:/allure-results:ro      |
    | volume  | allure-cli-report:/allure-report           |

  Then Directory "allure-cli-report" contains Allure HTML report with index.html
  And Allure HTML report contains scenario name "Passing"
