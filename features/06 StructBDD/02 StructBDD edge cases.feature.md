# Feature: StructBDD edge cases
  Verify StructBDD handling of HOCON, TOML, missing dependencies, and parse errors.

## Background:
* Given File "conftest.py" with content:
    ```python
    from pytest_bdd import given


    @given("a step")
    def _():
        pass
    ```
* And File "test_hocon.py" with content:
    ```python
    from pytest_bdd import scenarios

    test_scenarios = scenarios("test.bdd.hocon")
    ```
* And File "test_toml.py" with content:
    ```python
    from pytest_bdd import scenarios

    test_scenarios = scenarios("test.bdd.toml")
    ```

## Scenario: Parse HOCON StructBDD file
* Given StructBDD format is hocon
* When run pytest
    | cli_args | test_hocon.py |
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 1      |

## Scenario: Parse TOML StructBDD file
* Given StructBDD format is toml
* When run pytest
    | cli_args | test_toml.py |
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 1      |

## Scenario: StructBDD deserialization error on malformed input
* Given File "test_malformed.py" with content:
    ```python
    from pytest_bdd import scenarios

    test_scenarios = scenarios("struct.bdd.yaml")
    ```
* And StructBDD parse error occurs
* When run pytest
    | cli_args | test_malformed.py |
* Then StructBDD deserialization fails with expected error

@struct-bdd
## Scenario: StructBDD skipped when not installed
* Given File "test_skip.py" with content:
    ```python
    from pytest_bdd import scenarios

    test_scenarios = scenarios("test.bdd.yaml")
    ```
* And StructBDD format is yaml
* When run pytest
    | cli_args | test_skip.py -p no:pytest-bdd-struct-bdd |
* Then skipped gracefully
