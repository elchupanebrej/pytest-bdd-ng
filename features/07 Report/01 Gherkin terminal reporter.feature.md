# Feature: Gherkin terminal reporter
  This feature documents human-readable terminal reporting for feature and
  scenario execution outcomes.

## Scenario: Verbose reporter shows feature and scenario names
* Given File "test.feature" with content:

    ```gherkin
    Feature: Gherkin terminal output feature
      Scenario: Scenario example 1
        Given there is a bar
        When the bar is accessed
        Then world explodes
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given, when, then

    @given("there is a bar")
    def _bar():
      return "bar"

    @when("the bar is accessed")
    def _accessed():
      pass

    @then("world explodes")
    def _explodes():
      pass
    ```

* When run pytest

    | cli_args | --gherkin-terminal-reporter | -v |
    |----------|-----------------------------|----|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

* And pytest outcome must match lines:

    | *Feature: Gherkin terminal output feature* |
    | *Scenario: Scenario example 1* |
