# Feature: Summary formatter
  Verify behavior of the Summary formatter.

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

## Scenario: Summary shows run statistics
* When run pytest with summary formatter
* Then Summary output contains 1 passed

## Scenario: Summary shows duration
* When run pytest with summary formatter
* Then Summary output contains m

## Scenario: Summary shows failed test count
* Given File "test.feature.md" with content:
    ```markdown
    # Feature: Test feature
    ## Scenario: Test scenario
    * Given a failing step
    ```
* And File "conftest.py" with content:
    ```python
    from pytest_bdd import given
    @given("a failing step")
    def _fail():
        assert False
    ```
* When run pytest with summary formatter
* Then Summary output contains 1 failed
