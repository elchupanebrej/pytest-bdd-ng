Feature: Non-strict gherkin
^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents relaxed parsing behavior for user-facing Gherkin
files where scenarios can execute with ``When`` steps only, both from
``Background`` and from direct scenario steps.

Scenario: Execute non-strict Gherkin background and scenario sections
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File "no_strict_background.feature" with content:

  .. code:: gherkin

     Feature: No strict Gherkin Background support
       Background:
         When foo has a value "bar"
         And foo is not boolean
         And foo has not a value "baz"

       Scenario: Test background

- And File "no_strict_scenario.feature" with content:

  .. code:: gherkin

     Feature: No strict Gherkin Scenario support
       Scenario: Test scenario
         When foo has a value "bar"
         And foo is not boolean
         And foo has not a value "baz"

- And File "conftest.py" with content:

  .. code:: python

     import pytest
     from pytest_bdd import when

     @pytest.fixture
     def foo():
       return {}

     @when('foo has a value "bar"')
     def _bar(foo):
       foo["bar"] = "bar"
       assert foo["bar"] == "bar"

     @when('foo is not boolean')
     def _not_boolean(foo):
       assert foo is not bool

     @when('foo has not a value "baz"')
     def _has_not_baz(foo):
       assert "baz" not in foo

- And File "test_no_strict.py" with content:

  .. code:: python

     from pytest_bdd import scenario

     @scenario("no_strict_background.feature", "Test background")
     def test_background_no_strict():
       pass

     @scenario("no_strict_scenario.feature", "Test scenario")
     def test_scenario_no_strict():
       pass

- When run pytest

  \| cli_args \| -k \| test_no_strict.py \|

- Then pytest outcome must contain tests with statuses:

  ====== ======
  passed failed
  ====== ======
  2      0
  ====== ======
