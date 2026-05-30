# Feature: Report gathering outputs
  This feature documents generation of machine-readable and HTML reports during
  feature execution.
## Background:
* Given File "Passing.feature" with content:

    ```gherkin
    Feature: Passing feature
      Scenario: Passing scenario
        Given Passing step
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import step

    @step('Passing step')
    def _():
      ...
    ```

## Scenario: NDJson(JSONL) could be produced on the feature run

Output file could be fed into other @cucumber tools for more verbose report
[Messages](https://github.com/cucumber/messages)

* When run pytest

    <!-- markdownlint-disable-next-line MD013 -->
    | cli_args   |  --messages-ndjson | out.ndjson |
    |------------|------------|------------|
    | subprocess | true | |

* Then File "out.ndjson" has at least "15" lines
* Then Report "out.ndjson" parsable into messages

## Scenario: HTML report could be produced on the feature run

Dummy reporter based on [@cucumber/html-formatter](https://github.com/cucumber/html-formatter)

* Given Install npm packages

    | packages | @cucumber/html-formatter |
    |----------|--------------------------|

* When run pytest

    <!-- markdownlint-disable-next-line MD013 -->
    | cli_args   | --cucumber-html | out.html |
    |------------|-----------------|----------|
    | subprocess | true | |

* Then File "out.html" is not empty

## Scenario: Verbose reporting handles complex scenario parameters
* Given File "test.feature" with content:

    ```gherkin
    Feature: Report serialization containing parameters of complex types

      Scenario Outline: Complex
        Given there is a coordinate <point>

        Examples:
        | point |
        | 10,20 |
    ```

* And File "test_complex.py" with content:

    ```python
    import pytest
    from pytest_bdd import given, scenario, parsers

    class Point:
      def __init__(self, x, y):
        self.x = x
        self.y = y

      @classmethod
      def parse(cls, value):
        return cls(*(int(x) for x in value.split(",")))

    class Alien:
      pass

    @given(
      parsers.parse("there is a coordinate {point}"),
      target_fixture="point",
      converters={"point": Point.parse},
    )
    def _given_point(point):
      assert isinstance(point, Point)

    @pytest.mark.parametrize("alien", [Alien()])
    @scenario("test.feature", "Complex")
    def test_complex(alien):
      pass
    ```

* When run pytest

    | cli_args | -vvl | --disable-feature-autoload |
    |----------|------|----------------------------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

* And pytest outcome must match lines:

    | *test_complex.py::test_complex*alien0*PASSED* |
