# Feature: Cucumber JSON reporter
  This feature documents generation of Cucumber JSON reports for executed
  scenarios to support external reporting integrations.

## Scenario: Generate cucumber JSON with mixed pass/fail scenarios
* Given File "test.feature" with content:

    ```gherkin
    Feature: One passing scenario, one failing scenario
      Scenario: Passing
        Given a passing step

      Scenario: Failing
        Given a failing step
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given

    @given("a passing step")
    def _pass():
      return "pass"

    @given("a failing step")
    def _fail():
      raise Exception("Error")
    ```

* And File "test_report.py" with content:

    ```python
    from pytest_bdd import scenarios

    test_report = scenarios("test.feature")
    ```

* When run pytest

    | cli_args | -k | test_report.py | --cucumberjson=out.json | -s |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

* And File "out.json" is not empty
* And JSON file "out.json" jq query ".[0].elements[0].steps[0].result.status" returns "passed"
* And JSON file "out.json" jq query ".[0].elements[1].steps[0].result.status" returns "failed"
