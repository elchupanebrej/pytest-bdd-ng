# Feature: Code generation
  Verify that the code generator produces step definition scaffolds for undefined steps.

## Background:
* Given File "conftest.py" with content:
    ```python
    # No step definitions
    ```

## Scenario: Code generator produces step definition scaffolds
* Given File "undefined.feature.md" with content:
    ```markdown
    # Feature: Undefined
    ## Scenario: Missing steps
    * Given this step does not exist
    ```
* When run pytest
    | cli_args | --generate-missing | --feature | undefined.feature.md |
* Then generated Python code matches oracle:
    ```python
    from pytest_bdd import given

    @given("this step does not exist")
    def _():
        raise NotImplementedError
    ```

## Scenario: Generated code contains function definition
* Given File "undefined.feature.md" with content:
    ```markdown
    # Feature: Undefined
    ## Scenario: Missing steps
    * Given this step does not exist
    ```
* When run pytest
    | cli_args | --generate-missing | --feature | undefined.feature.md |
* Then generated Python code defines functions:
    | name |
    |------|
    | this_step_does_not_exist |

## Scenario: Generated code is printed to stdout not executed
* Given File "undefined.feature.md" with content:
    ```markdown
    # Feature: Undefined
    ## Scenario: Missing steps
    * Given this step does not exist
    ```
* When run pytest
    | cli_args | --generate-missing | --feature | undefined.feature.md |
* Then Generated code is printed to stdout

## Scenario: Code generator handles multiple undefined steps
* Given File "multiple.feature.md" with content:
    ```markdown
    # Feature: Undefined
    ## Scenario: Multiple missing steps
    * Given undefined step 1
    * When undefined step 2
    * Then undefined step 3
    ```
* When run pytest
    | cli_args | --generate-missing | --feature | multiple.feature.md |
* Then generated Python code matches oracle:
    ```python
    from pytest_bdd import given, then, when

    @given("undefined step 1")
    def _():
        raise NotImplementedError

    @when("undefined step 2")
    def _():
        raise NotImplementedError

    @then("undefined step 3")
    def _():
        raise NotImplementedError
    ```
