# Feature: Scenarios loader
  This feature documents loading multiple scenarios from one or more feature
  files, handling already-bound scenarios, and graceful skip behavior when no
  scenarios are found.

## Scenario: Load scenarios with `scenarios()` and keep bound scenario explicit
* Given File "pytest.ini" with fixture templated content:

    ```ini
    [pytest]
    console_output_style=classic
    bdd_features_base_dir={tmp_path}
    ```

* And File "test.feature" with content:

    ```gherkin
    Feature: Test scenarios
      Scenario: Test scenario
        Given I have a bar
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("I have a bar")
    def _bar():
        print("bar!")
        return "bar"
    ```

* And File "subfolder_test.feature" with content:

    ```gherkin
    Feature: Test scenarios
      Scenario: Test subfolder scenario
        Given I have a bar

      Scenario: Test failing subfolder scenario
        Given I have a failing bar

      Scenario: Test already bound scenario
        Given I have a bar

      Scenario: Test scenario
        Given I have a bar
    ```

* And File "test_scenarios.py" with content:

    ```python
    from pytest_bdd import scenarios, scenario

    test_feature = scenarios("subfolder_test.feature")


    @scenario("subfolder_test.feature", "Test already bound scenario")
    def test_already_bound():
        pass
    ```

* When run pytest

    | cli_args | -k | test_scenarios.py |
    | cli_args | -v |  |
* Then pytest outcome must contain tests with statuses:

    | passed | failed | skipped |
    |--------|--------|---------|
    | 4      | 1      | 2       |

* And pytest outcome must match lines:

    | *collected 7 items* |
    | *Test subfolder scenario* |
    | *Test failing subfolder scenario* |
    | *test_already_bound* |

## Scenario: Skip when no scenarios are found by `scenarios()`
* Given File "test_none.py" with content:

    ```python
    from pytest_bdd import scenarios

    test_feature = scenarios(".")
    ```

* When run pytest

    | cli_args | -k | test_none.py |
* Then pytest outcome must contain tests with statuses:

    | skipped | failed |
    |---------|--------|
    | 1       | 0      |
