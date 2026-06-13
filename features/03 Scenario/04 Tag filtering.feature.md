# Feature: Scenario tag filtering
  This feature documents tag-based scenario selection and verifies filtered
  execution behavior for CLI marker expressions, including tags after
  background sections.

## Scenario: Select scenarios by marker expression
* Given File "pytest.ini" with content:

    ```ini
    [pytest]
    markers =
        feature_tag_1
        feature_tag_2
        scenario_tag_01
        scenario_tag_02
        scenario_tag_10
        scenario_tag_20
    ```

* And File "tags.feature" with content:

    ```gherkin
    @feature_tag_1 @feature_tag_2
    Feature: Tags

      @scenario_tag_01 @scenario_tag_02
      Scenario: Tags
        Given I have a bar

      @scenario_tag_10 @scenario_tag_20
      Scenario: Tags 2
        Given I have a bar
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("I have a bar")
    def _bar():
        return "bar"
    ```

* When run pytest

    | cli_args | -m | scenario_tag_10 and not scenario_tag_01 | -vv |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

## Scenario: Keep tags working after background blocks
* Given File "pytest.ini" with content:

    ```ini
    [pytest]
    markers = tag
    ```

* And File "tags_after_background.feature" with content:

    ```gherkin
    Feature: Tags after background
      Background:
        Given I have a bar

      @tag
      Scenario: Tagged scenario
        Given I have a baz

      Scenario: Untagged scenario
        Given I have a baz
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd import given


    @given("I have a bar")
    def _bar():
        return "bar"


    @given("I have a baz")
    def _baz():
        return "baz"
    ```

* When run pytest

    | cli_args | -m | tag | -vv |

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
