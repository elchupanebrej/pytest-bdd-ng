# Feature: Step alias decorators

This feature documents alias behavior when one step function is decorated with
multiple step texts. It verifies that both aliases trigger the same underlying
function for `Given` and `When` steps.

## Scenario: Alias-decorated steps execute consistently
* Given File "alias.feature" with content:

    ```gherkin
    Feature: Step aliases
      Scenario: Multiple step aliases
        Given I have an empty list
        And I have foo (which is 1) in my list
        And I have bar (alias of foo) in my list
        When I do crash (which is 2)
        And I do boom (alias of crash)
        Then my list should be [1, 1, 2, 2]
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given, when, then


    @given("I have an empty list", target_fixture="results")
    def results():
        return []


    @given("I have foo (which is 1) in my list")
    @given("I have bar (alias of foo) in my list")
    def add_one(results):
        results.append(1)


    @when("I do crash (which is 2)")
    @when("I do boom (alias of crash)")
    def add_two(results):
        results.append(2)


    @then("my list should be [1, 1, 2, 2]")
    def check_results(results):
        assert results == [1, 1, 2, 2]
    ```

* And File "test_alias.py" with content:

    ```python
    from pytest_bdd import scenarios

    test_alias = scenarios("alias.feature")
    ```

* When run pytest

    | cli_args | -k | test_alias.py |
    |----------|----|---------------|
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
