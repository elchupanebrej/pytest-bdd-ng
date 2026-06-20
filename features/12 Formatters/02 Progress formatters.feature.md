# Feature: Progress formatters
  Verify behavior of Progress and Progress Bar formatters.

## Background:
* Given Cucumber formatters are available
* And File "test.feature.md" with content:
    ```markdown
    # Feature: Test feature
    ## Scenario: Test scenario 1
    * Given a passing step
    ## Scenario: Test scenario 2
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

    scenarios("test.feature.md")
    ```

## Scenario: Progress formatter shows output during run
* When run pytest

    | cli_args | --cucumber-progress |
    |----------|---------------------|
* Then Progress output shows .

## Scenario: Progress bar formatter shows bar during run
* When run pytest

    | cli_args | --cucumber-progress-bar |
    |----------|-------------------------|
* Then Progress output shows .

## Scenario: Progress formatter quiet mode
* When run pytest

    | cli_args | --cucumber-progress | -q |
    |----------|---------------------|----|
* Then Progress output shows .

## Scenario: Progress formatter verbose mode
* When run pytest

    | cli_args | --cucumber-progress | -v |
    |----------|---------------------|----|
* Then Progress output shows .
