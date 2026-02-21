# Feature: Step lifecycle and errors
  This feature documents step execution lifecycle and expected error reporting
  when step definitions are missing or when one function handles multiple steps.

## Scenario: Missing step definition produces a clear failure
* Given File "missing.feature" with content:

    ```gherkin
    Feature: Missing steps
      Scenario: Fails when no step implementation exists
        Given undefined step
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | failed |
    |--------|
    | 1      |

* And pytest outcome must match lines:

    | *StepDefinitionNotFoundError:* |

## Scenario: One function can serve multiple step aliases
* Given File "steps.feature" with content:

    ```gherkin
    Feature: Steps decoration
      Scenario: Step function can be decorated multiple times
        Given there is a foo with value 42
        And there is a second foo with value 43
        When I do nothing
        And I do nothing again
        Then I make no mistakes
        And I make no mistakes again
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given, when, then, parsers

    @given(parsers.parse("there is a foo with value {value}"), target_fixture="first_foo")
    @given(parsers.parse("there is a second foo with value {value}"), target_fixture="second_foo")
    def _foo(value):
      return value

    @when("I do nothing")
    @when("I do nothing again")
    def _do_nothing(first_foo, second_foo):
      assert first_foo == "42"
      assert second_foo == "43"

    @then("I make no mistakes")
    @then("I make no mistakes again")
    def _no_errors(first_foo, second_foo):
      assert first_foo == "42"
      assert second_foo == "43"
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
