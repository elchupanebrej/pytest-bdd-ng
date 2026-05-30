# Feature: Code generation
  Verify that the code generator produces step definition scaffolds for undefined steps.

## Background:
* Given Feature file with undefined steps
* And File "conftest.py" with content:
    ```python
    # No step definitions
    ```

## Scenario: Code generator produces step definition scaffolds
* When run pytest with code generator
* Then Generated code contains @step

## Scenario: Generated code contains function definition
* When run pytest with code generator
* Then Generated code contains def _

## Scenario: Generated code is printed to stdout not executed
* When run pytest with code generator
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
* When run pytest with code generator
* Then Generated code contains @step
