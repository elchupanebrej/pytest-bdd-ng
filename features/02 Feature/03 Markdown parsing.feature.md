# Feature: Markdown parsing
  This feature documents parsing Gherkin content embedded in Markdown files so
  executable documentation can live alongside narrative docs while still
  executing step-by-step behavior assertions.

## Scenario: Parse and execute Markdown-based Gherkin steps
* Given File "steps.feature.md" with content:

    ```markdown
    # Feature: Steps are executed one by one

    Steps are executed one by one. Given and When sections
    are not mandatory in some cases.

    ## Scenario: Executed step by step
    * Given I have a foo fixture with value "foo"
    * And there is a list
    * When I append 1 to the list
    * And I append 2 to the list
    * And I append 3 to the list
    * Then foo should have value "foo"
    * But the list should be [1, 2, 3]
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given, when, then


    @given('I have a foo fixture with value "foo"', target_fixture="foo")
    def _foo():
        return "foo"


    @given("there is a list", target_fixture="results")
    def _results():
        return []


    @when("I append 1 to the list")
    def _append_1(results):
        results.append(1)


    @when("I append 2 to the list")
    def _append_2(results):
        results.append(2)


    @when("I append 3 to the list")
    def _append_3(results):
        results.append(3)


    @then('foo should have value "foo"')
    def _foo_is_foo(foo):
        assert foo == "foo"


    @then("the list should be [1, 2, 3]")
    def _check_results(results):
        assert results == [1, 2, 3]
    ```

* And File "test_sample.py" with content:

    ```python
    from pytest_bdd import scenarios

    test = scenarios("steps.feature.md")
    ```

* When run pytest

    | cli_args | -k | test_sample.py |
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
