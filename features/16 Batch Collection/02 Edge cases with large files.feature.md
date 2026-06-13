# Feature: Batch collection edge cases with large files
  Verify batch parser handles multiple files and explicit bindings coexist with batch collection.

## Background:
* Given File "test1.feature" with content:
    ```gherkin
    Feature: Test 1
        Scenario: Test 1
            Given a passing step
    ```
* And File "test2.feature" with content:
    ```gherkin
    Feature: Test 2
        Scenario: Test 2
            Given a passing step
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

    scenarios(".")
    ```

## Scenario: Batch collection discovers multiple feature files via directory scan
* When run pytest
* Then Batch collection processes 2 files
