# Feature: Features could be tagged
  For picking up tests to run we can use [tests selection](http://pytest.org/latest/usage.html#specifying-tests-selecting-tests)
  technique.
  The problem is that you have to know how your tests are organized,
  knowing only the feature files organization is not enough.
  [cucumber tags](https://github.com/cucumber/cucumber/wiki/Tags) introduces
  standard way of categorizing your features and scenarios.

## Rule:
### Background:
* Given File "Passed.feature" with content:

    ```gherkin
    @passed
    Feature: Steps are executed by corresponding step keyword decorator
      Scenario: Passed
        Given I produce passed test
    ```

* Given File "Failed.feature" with content:

    ```gherkin
    @failed
    Feature: Steps are executed by corresponding step keyword decorator
      Scenario: Failed
        Given I produce failed test
    ```

* Given File "Both.feature" with content:

    ```gherkin
    @both
    Feature: Steps are executed by corresponding step keyword decorator
      Scenario: Passed
        Given I produce passed test

      Scenario: Failed
        Given I produce failed test
    ```

* Given File "pytest.ini" with content:

    ```ini
    [pytest]
    markers =
      passed
      failed
      both
    ```

* And File "conftest.py" with content:

    ```python
    from pytest_bdd.compatibility.pytest import fail
    from pytest_bdd import given


    @given("I produce passed test")
    def passing_step(): ...


    @given("I produce failed test")
    def failing_step():
        fail("Enforce fail")
    ```

### Scenario: Run pytest with marker passed
* When run pytest

    | cli_args | -m | passed |
    |----------|----|--------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |

### Scenario: Run pytest with marker failed
* When run pytest

    | cli_args | -m | failed |
    |----------|----|--------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 0      | 1      |

### Scenario: Run pytest with marker passed or failed
* When run pytest

    | cli_args | -m | passed or failed |
    |----------|----|------------------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Scenario: Run pytest with marker not both
* When run pytest

    | cli_args | -m | not both |
    |----------|----|----------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Scenario: Run pytest with marker both
* When run pytest

    | cli_args | -m | both |
    |----------|----|------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Scenario: Run pytest with no marker
* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 2      | 2      |
