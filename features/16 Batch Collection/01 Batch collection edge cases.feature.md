# Feature: Batch collection edge cases
  Verify batch parser correctly handles caches, flags, empty directories, and malformed files.

## Background:
* Given File "test1.feature.md" with content:
    ```markdown
    # Feature: Test 1
    ## Scenario: Test 1
    * Given a passing step
    ```
* And File "test2.feature.md" with content:
    ```markdown
    # Feature: Test 2
    ## Scenario: Test 2
    * Given a passing step
    ```
* And File "test3.feature.md" with content:
    ```markdown
    # Feature: Test 3
    ## Scenario: Test 3
    * Given a passing step
    ```
* And File "conftest.py" with content:
    ```python
    from pytest_bdd import given


    @given("a passing step")
    def _pass():
        pass
    ```
* And File "test_sample.py" with content:
    ```python
    from pytest_bdd import scenarios

    scenarios(".")
    ```

## Scenario: Batch collection processes multiple files
* When run pytest
* Then Batch collection processes 3 files

## Scenario: Batch collection cache is used on second run
* Given Batch collection cache is enabled
* When run pytest
* Then Batch collection cache is used

## Scenario: Batch collection flag can disable batch mode
* When run pytest
    | cli_args | --disable-batch-collection |
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 3      |

## Scenario: Batch collection handles empty feature directory
* Given File "empty_test.py" with content:
    ```python
    from pytest_bdd import scenarios

    scenarios("empty_dir")
    ```
* When run pytest
* Then pytest outcome must contain tests with statuses:
    | passed |
    |--------|
    | 3      |

## Scenario: Batch collection handles malformed feature file
* Given File "malformed.feature.md" with content:
    ```markdown
    # Not a feature
    ```
* Given File "test_malformed.py" with content:
    ```python
    from pytest_bdd import scenarios

    scenarios("malformed.feature.md")
    ```
* When run pytest
    | cli_args | test_malformed.py |
* Then pytest outcome must contain tests with statuses:
    | failed |
    |--------|
    | 0      |
