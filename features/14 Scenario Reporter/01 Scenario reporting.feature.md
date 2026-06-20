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
    import json
    from pathlib import Path

    from pytest_bdd import given


    @given("a passing step")
    def _pass():
        pass


    @given("I attach data")
    def attach_data(attach):
        attach("scenario evidence", media_type="text/plain")


    def pytest_runtest_logreport(report):
        scenario = getattr(report, "scenario", None)
        if report.when == "call" and scenario is not None:
            Path("scenario-reports.jsonl").open("a", encoding="utf-8").write(json.dumps(scenario) + "\n")
    ```
* And File "test_sample.py" with content:
    ```python
    from pytest_bdd import scenarios

    test_scenarios = scenarios("test.feature.md")
    ```
* And File "pytest.toml" with content:
    ```toml
    [pytest]
    bdd_features_base_dir = .
    ```

## Scenario: Scenario reporter records scenario name
* When run pytest with scenario reporter
* Then scenario report contains scenario "Test scenario"

## Scenario: Scenario reporter records scenario that uses attachments
* Given Scenario with attachment
* When run pytest with scenario reporter
* Then scenario report contains scenario "With attach"

## Scenario: Scenario reporter records passed scenario
* When run pytest with scenario reporter
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
