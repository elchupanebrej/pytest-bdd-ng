# Feature: Heading validation
  Feature and Scenario names must be provided in valid .feature.md files.

## Scenario: Empty feature heading is detected
* Given Feature file has empty heading
* When collect feature files
* Then heading validation skips invalid heading

## Scenario: Empty scenario heading is detected
* Given Feature file has empty scenario heading
* When collect feature files
* Then heading validation skips invalid heading

## Scenario: Valid headings pass validation
* Given File "valid.feature.md" with content:
    ```markdown
    # Feature: Valid feature heading
    ## Scenario: Valid scenario heading
    * Given a valid step
    ```
* And File "conftest.py" with content:
    ```python
    from pytest_bdd import given


    @given("a valid step")
    def _pass():
        pass
    ```
* And File "test_valid.py" with content:
    ```python
    from pytest_bdd import scenarios

    scenarios("valid.feature.md")
    ```
* When run pytest

    | cli_args | -k | valid |
    |----------|----|-------|
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
