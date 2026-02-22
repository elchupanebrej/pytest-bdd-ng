# Feature: HTTP feature loading
  This feature documents loading Gherkin feature files over HTTP and executing
  scenarios as regular pytest tests, including explicit URL mode and
  base-URL resolution mode.

## Scenario: Load feature from explicit HTTP URL
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "test_http.py" with fixture templated content:

    ```python
    from pytest_bdd import given, scenarios, FeaturePathType
    from pytest_bdd.mimetype import Mimetype

    @given("I have 42 cukes in my belly")
    def _results():
      pass

    test_cukes = scenarios(
      "http://localhost:{httpserver_port}/feature",
      features_mimetype=Mimetype.gherkin_plain,
      features_path_type=FeaturePathType.URL,
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Load feature using HTTP base URL from pytest.ini
* Given Localserver endpoint "/feature" responding content:

    ```gherkin
    Feature: minimal
      Scenario: Passing cukes
        Given I have 42 cukes in my belly
    ```

* And File "test_http.py" with fixture templated content:

    ```python
    from pytest_bdd import scenarios
    from pytest_bdd import given

    @given("I have 42 cukes in my belly")
    def _results():
      pass

    test_cukes = scenarios(
      "/feature",
      features_base_url="http://localhost:{httpserver_port}",
    )
    ```

* When run pytest

    | cli_args | -k | test_http.py |
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
