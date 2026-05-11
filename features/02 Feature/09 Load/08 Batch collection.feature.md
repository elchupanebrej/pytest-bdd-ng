# Feature: Batch feature file collection
  To reduce collection latency for projects with many `.feature` files,
  pytest-bdd-ng reads and parses files concurrently using asyncio and
  multiprocessing Pool when the file count meets the configured threshold.
  Below the threshold, synchronous single-file parsing is used to avoid
  Pool startup overhead. This feature documents the flags and options
  controlling batch collection behavior.

## Rule: Batch collection control
### Background:
* Given File "Passing.feature" with content:

    ```gherkin
    Feature: Passing feature
      Scenario: Passing scenario
        * Passing step
    ```

* Given File "Another.passing.feature" with content:

    ```gherkin
    Feature: Another passing feature
      Scenario: Another passing scenario
        * Passing step
    ```

* Given File "Third.passing.feature" with content:

    ```gherkin
    Feature: Third passing feature
      Scenario: Third passing scenario
        * Passing step
    ```

* Given File "conftest.py" with content:

    ```python
    from pytest_bdd import step

    @step('Passing step')

    def _():
      ...
    ```

### Scenario: Batch collection is enabled by default
* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 3      |

### Scenario: Batch collection can be disabled via command line.
* When run pytest

    | cli_args | --disable-batch-collection |
    |----------|----------------------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 3      |

### Scenario: Batch collection can be disabled via pytest.ini
* Given Set pytest.ini content to:

    ```ini
    [pytest]
    disable_batch_collection=true
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 3      |

### Scenario: Batch threshold can be set via pytest.ini
* Given Set pytest.ini content to:

    ```ini
    [pytest]
    batch_threshold=1
    ```

* When run pytest
* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 3      |

### Scenario: Explicit scenario binding still works with batch disabled
* Given File "test_explicit.py" with content:

    ```python
    from pytest_bdd import scenario

    @scenario("Passing.feature", "Passing scenario")
    def test_explicit():
      pass
    ```

* When run pytest

    | cli_args | --disable-batch-collection | --disable-feature-autoload |
    |----------|----------------------------|----------------------------|

* Then pytest outcome must contain tests with statuses:

    | passed |
    |--------|
    | 1      |
