# Feature: Allure scenario reporting
  This feature documents Allure reporting for regular scenarios and validates
  plugin-gated execution when Allure integration is unavailable.

## Scenario: Scenario reporting is guarded by Allure availability
* Given Copy path from "features/07 Report/06 Allure/01 scenario.feature" to test path "scenario.feature"

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("passing step")
    def _(): ...
    ```

* And File "test_sample.py" with content:

    ```python
    import pytest
    from pytest_bdd import scenarios
    from pytest_bdd.compatibility.allure import ALLURE_INSTALLED

    pytestmark = [pytest.mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")]
    test = scenarios("scenario.feature")
    ```

* When run pytest

    | cli_args | -k test_sample.py |
    |----------|-------------------|

* Then pytest outcome must contain tests with statuses:

    | skipped |
    |---------|
    | 1       |
