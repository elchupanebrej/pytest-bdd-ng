# Feature: Cucumber Formatter Renderer CLI
  Verify the render_cucumber_formatters CLI tool renders formatters from an NDJSON message stream.

## Scenario: Render cucumber summary from NDJSON messages
  * Given File "test.feature.md" with content:

    ```gherkin
    # Feature: Simple pass
    ## Scenario: Pass scenario
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
    test = scenarios("test.feature.md", features_base_dir=".")
    ```
  * And run pytest

    | cli_args | test_sample.py | --messages-ndjson | messages.ndjson |
  * When run `python -m pytest_bdd.script.render_cucumber_formatters --messages-ndjson messages.ndjson --cucumber-summary`
  * Then the command exit code is 0
  * And the renderer terminal output includes:
    | 1 scenario (1 passed) |
    | 1 step (1 passed) |
