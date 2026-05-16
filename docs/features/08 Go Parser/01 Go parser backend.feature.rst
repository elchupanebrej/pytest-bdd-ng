Feature: Go parser backend
^^^^^^^^^^^^^^^^^^^^^^^^^^

Test that Go parser is utilized successfully, falls back gracefully, and
correctly selects backend.

Background:
'''''''''''

- Given File "test.feature.md" with content:

  .. code:: markdown

     # Feature: Test
     ## Scenario: Test
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

Scenario: Parse succeeds when Go library is available
'''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given Go parser shared library is built
- When run pytest with Go backend
- Then pytest outcome must contain tests with statuses: \| passed \|
  \|--------\| \| 1 \|

Scenario: Falls back to Python parser when Go unavailable
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given Go parser is not available
- When run pytest with Python backend
- Then pytest outcome must contain tests with statuses: \| passed \|
  \|--------\| \| 1 \|

Scenario: Go parser version is logged on first use
''''''''''''''''''''''''''''''''''''''''''''''''''

- Given Go parser shared library is built
- Then Go parser version is logged

Scenario: Environment variable controls backend selection
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File "pytest.ini" with content:

  .. code:: ini

     [pytest]

- When run pytest with Python backend
- Then pytest outcome must contain tests with statuses: \| passed \|
  \|--------\| \| 1 \|
