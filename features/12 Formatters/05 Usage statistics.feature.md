# Feature: Usage statistics
  Verify behavior of the Usage and Usage JSON formatters.

## Background:
* Given Cucumber formatters are available
* And File "test.feature.md" with content:
    ```markdown
    # Feature: Test feature
    ## Scenario: Test scenario
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

## Scenario: Usage formatter shows step definition counts
* When run pytest with usage formatter
* Then Usage output shows 1 step definitions used

## Scenario: Usage JSON formatter produces valid JSON
* When run pytest with usage JSON formatter
* Then Usage JSON is valid

## Scenario: Usage detects unused step definitions
* Given File "conftest.py" with content:
    ```python
    from pytest_bdd import given


    @given("a passing step")
    def _pass():
        pass


    @given("an unused step")
    def _unused():
        pass
    ```
* When run pytest with usage formatter
* Then Usage output shows 2 step definitions used
* And Usage output shows 0 step definitions used

## Scenario: Usage JSON contains step match counts
* When run pytest with usage JSON formatter
* Then Usage JSON is valid
