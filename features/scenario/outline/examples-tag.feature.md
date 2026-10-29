# Feature: Scenario Outline examples could be tagged
## Rule:
### Background:
* Given File "steps.feature" with content:
    ```gherkin
    Feature: Steps are executed by corresponding step keyword decorator

      Scenario Outline:
          Given I produce <outcome> test

          @passed
          Examples:
          |outcome|
          |passed |

          @failed
          Examples:
          |outcome|
          |failed |

          @both
          Examples:
          |outcome|
          |passed |
          |failed |
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
    from pytest_cuke.compatibility.pytest import fail
    from pytest_cuke import given

    @given('I produce passed test')
    def passing_step():
      ...

    @given('I produce failed test')
    def failing_step():
      fail('Enforce fail')
    ```

### Scenario:
* When I run pytest with arguments "-m passed"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 1      | 0      |

### Scenario:
* When I run pytest with arguments "-m failed"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 0      | 1      |

### Scenario:
* When I run pytest with arguments "-m 'passed or failed'"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Scenario:
* When I run pytest with arguments "-m 'not both'"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Scenario:
* When I run pytest with arguments "-m both"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Scenario:
* When run pytest
* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 2      | 2      |

## Rule: Mixing tags on feature & examples level
### Background:
* Given File "steps.feature" with content:
    ```gherkin
    @feature_tag
    Feature: Steps are executed by corresponding step keyword decorator
      Scenario Outline:
          Given I produce <outcome> test

          Examples:
          |outcome|
          |passed |

          @examples_tag
          Examples:
          |outcome|
          |failed |
    ```
* Given File "pytest.ini" with content:
    ```ini
    [pytest]
    markers =
      feature_tag
      examples_tag
    ```
* And File "conftest.py" with content:
    ```python
    from pytest_cuke.compatibility.pytest import fail
    from pytest_cuke import given

    @given('I produce passed test')
    def passing_step():
      ...

    @given('I produce failed test')
    def failing_step():
      fail('Enforce fail')
    ```

### Example:
* When I run pytest with arguments "-m feature_tag"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 1      | 1      |

### Example:
* When I run pytest with arguments "-m examples_tag"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 0      | 1      |

### Example:
* When I run pytest with arguments "-m 'not feature_tag'"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 0      | 0      |

### Example:
* When I run pytest with arguments "-m 'not examples_tag'"

* Then pytest outcome must contain tests with statuses:
    | passed | failed |
    |--------|--------|
    | 1      | 0      |

### Example:
* When I run pytest with arguments "-m feature_tag --collect-only"

* Then pytest outcome must match lines:
    | collected 2 items |
    |-------------------|

### Example:
* When I run pytest with arguments "-m examples_tag --collect-only"

* Then pytest outcome must match lines:
    | collected 2 items / 1 deselected / 1 selected |
    |-----------------------------------------------|

### Example:
* When I run pytest with arguments "-m 'not feature_tag' --collect-only"

* Then pytest outcome must match lines:
    | collected 2 items / 2 deselected* |
    |-----------------------------------|

### Example:
* When I run pytest with arguments "-m 'not examples_tag' --collect-only"

* Then pytest outcome must match lines:
    | collected 2 items / 1 deselected / 1 selected |
    |-----------------------------------------------|
