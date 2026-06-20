# Feature: Feature base directory resolution
  This feature documents how pytest-bdd resolves feature paths from configuration
  and from explicit `features_base_dir` parameters, including precedence rules.

## Background:
* Given File "steps.feature" with content:

    ```gherkin
    Feature: Feature path
      Scenario: When scenario found
        Given found
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("found")
    def _(): ...
    ```

* And File "test_feature.py" with content:

    ```python
    import pytest

    from pytest_bdd import scenario, scenarios

    FEATURE = "steps.feature"


    def assert_generated_test(test_obj):
        # Explicit assertion that scenario binding produced a pytest test callable.
        assert callable(test_obj)
        assert test_obj.__name__.startswith("test_")
        assert any(mark.name == "scenarios" for mark in getattr(test_obj, "pytestmark", []))


    @pytest.fixture(params=["When scenario found"])
    def scenario_name(request):
        return request.param


    @pytest.mark.parametrize("multiple", [True, False])
    def test_ok_by_ini(scenario_name, multiple):
        # This verifies ini-driven base-directory resolution.
        if multiple:
            generated = scenarios(FEATURE)
        else:
            generated = scenario(FEATURE, scenario_name, return_test_decorator=False)
        assert_generated_test(generated)


    @pytest.mark.parametrize("multiple", [True, False])
    def test_ok_by_param(scenario_name, multiple):
        # This verifies explicit per-call override of base directory.
        if multiple:
            generated = scenarios(FEATURE, features_base_dir="features")
        else:
            generated = scenario(FEATURE, scenario_name, features_base_dir="features", return_test_decorator=False)
        assert_generated_test(generated)
    ```

### Scenario: Resolve by ini-configured base directory
* Given Set pytest.ini content to:

    ```ini
    [pytest]
    bdd_features_base_dir=features
    ```

* When run pytest

    | cli_args | -k | test_ok_by_ini |
    |----------|----|----------------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed | skipped |
    |--------|--------|---------|
    | 2      | 0      | 0       |

### Scenario: Explicit argument overrides invalid ini base directory
* Given Set pytest.ini content to:

    ```ini
    [pytest]
    bdd_features_base_dir=/does/not/exist
    ```

* When run pytest

    | cli_args | -k | test_ok_by_param |
    |----------|----|------------------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed | skipped |
    |--------|--------|---------|
    | 2      | 0      | 0       |
