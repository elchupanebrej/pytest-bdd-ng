# Feature: Scenario reporting
  Verify behavior of the scenario reporter plugin.

## Background:
* Given File "test.feature.md" with content:
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
* And File "pytest.ini" with content:
    ```ini
    [pytest]
    bdd_features_base_dir = .
    ```

## Scenario: Scenario reporter outputs scenario name
* When run pytest with scenario reporter
* Then Scenario reporter outputs scenario name

## Scenario: Scenario reporter handles attachments
* Given Scenario with attachment
* When run pytest with scenario reporter
* Then Attachment is recorded

## Scenario: Scenario reporter outputs for passed scenario
* When run pytest with scenario reporter
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 1      |
