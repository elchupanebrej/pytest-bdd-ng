# Feature: Snippets formatter
  Verify snippets formatter outputs suggestions for undefined steps.

## Background:
* Given Cucumber formatters are available
* And File "test.feature.md" with content:
    ```markdown
    # Feature: Test feature
    ## Scenario: Test scenario
    * Given an undefined step
    ```
* And File "conftest.py" with content:
    ```python
    # No step definitions
    ```
* And File "test_sample.py" with content:
    ```python
    from pytest_bdd import scenarios
    scenarios("test.feature.md")
    ```

## Scenario: Snippets formatter suggests undefined step
* When run pytest with snippets formatter
* Then Snippet output suggests step definition for an undefined step

## Scenario: Snippet template format is correct
* When run pytest with snippets formatter
* Then Snippet output suggests step definition for @given
