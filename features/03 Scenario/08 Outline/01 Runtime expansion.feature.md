# Feature: Outline runtime expansion
  This feature documents expansion of scenario outline examples into executable
  tests at runtime, including multiplication by regular pytest fixture
  parametrization.

## Scenario: Outline examples expand with parametrized fixtures
* Given File "outline.feature" with content:

    ```gherkin
    Feature: Outline
      Scenario Outline: Outlined given, when, thens
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

        Examples:
          | start | eat | left |
          | 12    | 5   | 7    |
          | 5     | 4   | 1    |
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given, when, then, parsers


    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
    def _start_cucumbers(start):
        assert isinstance(start, int)
        return {"start": start}


    @when(parsers.parse("I eat {eat:g} cucumbers"))
    def _eat_cucumbers(start_cucumbers, eat):
        assert isinstance(eat, float)
        start_cucumbers["eat"] = eat


    @then(parsers.parse("I should have {left} cucumbers"))
    def _should_have_left_cucumbers(start_cucumbers, start, eat, left):
        assert start - eat == int(left)
        assert start_cucumbers["start"] == start
        assert start_cucumbers["eat"] == eat
    ```

* And File "test_outline.py" with content:

    ```python
    from pytest import fixture
    from pytest_bdd import scenario


    @fixture(params=[1, 2, 3])
    def other_fixture(request):
        return request.param


    @scenario("outline.feature", "Outlined given, when, thens")
    def test_outline(other_fixture):
        pass
    ```

* When run pytest

    | cli_args | -k | test_outline.py |
    |----------|----|-----------------|
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 6      | 0      |

## Scenario: Invalid outline example table reports parsing error
* Given File "outline.feature" with content:

    ```gherkin
    Feature: Outline
      Scenario Outline: Outlined with wrong vertical example table
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

        Examples:
        | start | eat | left |
        | 12    | 10  | 7    |
        | 2     | 1   |
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import parsers, given, when, then


    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
    def _start_cucumbers(start):
        return {"start": start}


    @when(parsers.parse("I eat {eat:g} cucumbers"))
    def _eat_cucumbers(start_cucumbers, eat):
        start_cucumbers["eat"] = eat


    @then(parsers.parse("I should have {left} cucumbers"))
    def _left_cucumbers(start_cucumbers, start, eat, left):
        assert start - eat == int(left)
        assert start_cucumbers["start"] == start
        assert start_cucumbers["eat"] == eat
    ```

* When run pytest

    | cli_args | -k | outline.feature |
    |----------|----|-----------------|
* Then pytest outcome must contain tests with statuses:

    | errors |
    |--------|
    | 1      |

* And pytest outcome must match lines:

    | *FeatureConcreteParseError* |
    |-----------------------------|
