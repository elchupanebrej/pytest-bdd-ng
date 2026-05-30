Feature: Python version compatibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Verify compatibility checks and shims for older Python/pytest versions.

Background:
'''''''''''

- Given File "test.feature.md" with content:

  .. code:: markdown

     # Feature: Test feature
     ## Scenario: Test scenario
     * Given a passing step

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import given
     @given("a passing step")
     def _pass():
         pass

- And File "test_sample.py" with content:

  .. code:: python

     from pytest_bdd import scenarios
     scenarios("test.feature.md")

Scenario: Pytest version compatibility holds for supported range
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- When run pytest
- Then Pytest version compatibility holds

Scenario: StrEnum behavior is consistent across Python versions
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Then StrEnum behavior is consistent

Scenario: Pytest mark expression parsing works
''''''''''''''''''''''''''''''''''''''''''''''

- Given Pytest mark expression is "smoke and not slow"
- When run pytest \| cli_args \| -m \| smoke and not slow \|
- Then pytest outcome must contain tests with statuses: \| passed \|
  \|--------\| \| 0 \|
