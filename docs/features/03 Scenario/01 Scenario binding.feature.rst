Feature: Scenario binding
^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents binding a Python test to a named scenario and
verifies both successful binding and graceful skip behavior when a named
scenario does not exist.

Scenario: Bind a test function to an existing scenario
''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File "simple.feature" with content:

  .. code:: gherkin

     Feature: Simple feature
       Scenario: Simple scenario
         Given I have a bar

- And File "test_simple.py" with content:

  .. code:: python

     from pathlib import Path
     from pytest_bdd import scenario

     @scenario(Path(__file__).parent / "simple.feature", "Simple scenario")
     def test_simple():
       pass

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import given

     @given("I have a bar")
     def _bar():
       return "bar"

- And File "pytest.ini" with content:

  .. code:: ini

     [pytest]
     bdd_features_base_dir=missing

- When run pytest

  \| cli_args \| -k \| test_simple.py \|

- Then pytest outcome must contain tests with statuses:

  ====== ======
  passed failed
  ====== ======
  1      0
  ====== ======

Scenario: Skip when bound scenario is missing
'''''''''''''''''''''''''''''''''''''''''''''

- Given File "not_found.feature" with content:

  .. code:: gherkin

     Feature: Scenario is not found

- And File "test_not_found.py" with content:

  .. code:: python

     from pathlib import Path
     from pytest_bdd import scenario

     @scenario(Path(__file__).parent / "not_found.feature", "Missing scenario")
     def test_missing():
       pass

- And File "pytest.ini" with content:

  .. code:: ini

     [pytest]
     bdd_features_base_dir=missing

- When run pytest

  \| cli_args \| -k \| test_not_found.py \|

- Then pytest outcome must contain tests with statuses:

  ======= ======
  skipped failed
  ======= ======
  1       0
  ======= ======
