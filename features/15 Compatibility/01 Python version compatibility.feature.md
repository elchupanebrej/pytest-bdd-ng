# Feature: Python version compatibility
  Verify compatibility checks and shims for older Python/pytest versions.

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
    scenarios("test.feature.md")
    ```

## Scenario: Pytest version compatibility holds for supported range
* When run pytest
* Then Pytest version compatibility holds

## Scenario: Pytest mark expression parsing works
* Given File "test_mark_expression.py" with content:
    ```python
    import pytest

    @pytest.mark.smoke
    def test_smoke_selected():
        pass

    @pytest.mark.smoke
    @pytest.mark.slow
    def test_slow_rejected():
        pass
    ```
* Given Pytest mark expression is "smoke and not slow"
* When run pytest
    | cli_args | test_mark_expression.py | -m | smoke and not slow |
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 1      |
