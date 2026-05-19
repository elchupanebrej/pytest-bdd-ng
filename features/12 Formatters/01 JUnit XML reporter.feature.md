# Feature: JUnit XML reporter
  Verify JUnit XML formatter behavior and report structure.

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
    test_scenarios = scenarios("test.feature.md")
    ```

## Scenario: JUnit XML output contains test suite structure
* When run pytest with JUnit reporter
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 2      |
* And File "report.xml" contains the line "<testsuite"

## Scenario: JUnit XML contains test case elements
* When run pytest with JUnit reporter
* Then File "report.xml" contains the line "<testcase"

## Scenario: JUnit XML contains failure element on failed test
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
* When run pytest with JUnit reporter
* Then File "report.xml" contains the line "<failure"

## Scenario: JUnit XML output is valid XML
* When run pytest with JUnit reporter
* Then File "report.xml" contains the line "<?xml version="
