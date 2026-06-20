# Feature: Gherkin features autoload
  By default Gherkin features in the test hierarchy are collected as pytest
  tests. This feature documents how to disable autoload while still running
  explicitly bound scenarios.

## Rule: Feature autoload
### Background:
* Given File "Passing.feature" with content:

    ```gherkin
    Feature: Passing feature
      Scenario: Passing scenario
        * Passing step
    ```

* Given File "Another.passing.feature.md" with content:

    ```markdown
    # Feature: Passing feature
    ## Scenario: Passing scenario
    * Given Passing step
    ```

* Given File "conftest.py" with content:

    ```python
    from pytest_bdd import step


    @step("Passing step")
    def _(): ...
    ```

### Scenario: Feature is loaded by default
* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 2      |

### Scenario: Feature autoload could be disabled via command line
* When run pytest

    | cli_args | --disable-feature-autoload |
    |----------|----------------------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 0      |

### Scenario: Feature autoload could be disabled via pytest.toml
* Given Set pytest.toml content to:

    ```toml
    [pytest]
    disable_feature_autoload=true
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 0      |

### Scenario: Explicit scenario binding still runs when autoload is disabled
* Given File "test_explicit.py" with content:

    ```python
    from pytest_bdd import scenario


    @scenario("Passing.feature", "Passing scenario")
    def test_explicit():
        pass
    ```

* When run pytest

    | cli_args | --disable-feature-autoload |
    |----------|----------------------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |

### Scenario: Explicit binding supports features_base_dir while autoload is disabled
* Given File "steps.feature" with content:

    ```gherkin
    Feature: Explicit
      Scenario: Explicit from features dir
        Given explicit step
    ```

* Given File "test_explicit.py" with content:

    ```python
    from pytest_bdd import given, scenario


    @scenario("steps.feature", "Explicit from features dir", features_base_dir=".")
    def test_explicit_from_features_dir():
        pass


    @given("explicit step")
    def _explicit_step():
        pass
    ```

* When run pytest

    | cli_args | --disable-feature-autoload |
    |----------|----------------------------|

* Then pytest outcome must contain tests with statuses:

    | passed | failed |
    |--------|--------|
    | 1      | 0      |
