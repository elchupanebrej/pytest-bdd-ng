# Feature: HTTP feature MIME selection
  The public Mimetype enum and its string value select the same HTTP feature
  parser, so both binding forms produce the same scenarios.

## Rule: Equivalent MIME declarations
### Background:
* Given Localserver endpoint "/features/Named" responding content:
    ```gherkin
    Feature: Named feature
      Scenario: Passing scenario
        Given Passing step
      Scenario: Failing scenario
        Given Failing step
    ```
* And File "conftest.py" with content:
    ```python
    from pytest_cuke import step
    from pytest_cuke.compatibility.pytest import fail

    @step('Passing step')
    def _():
      ...

    @step('Failing step')
    def _():
      fail('Intentional')
    ```
* And File "test_enum.py" with content:
    ```python
    from pytest_cuke import scenarios
    from pytest_cuke.mimetypes import Mimetype

    test_enum = scenarios('Named', features_path_type='url', features_mimetype=Mimetype.gherkin_plain)
    ```
* And File "test_string.py" with content:
    ```python
    from pytest_cuke import scenarios

    test_string = scenarios(
        'Named',
        features_path_type='url',
        features_mimetype='text/x.cucumber.gherkin+plain',
    )
    ```

### Scenario: The Mimetype enum loads the same HTTP feature as the string
* Given File "pytest.ini" with fixture templated content:
    ```ini
    [pytest]
    cuke_features_base_url=http://localhost:{httpserver_port}/features
    ```
* When run pytest
* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 2      | 2      |
