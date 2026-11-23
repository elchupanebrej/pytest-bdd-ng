Feature: Autoload follows the pytest test tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Feature files that sit next to tests are collected by a plain pytest
run. An explicit binding wins when it and autoload name the same
scenario.

Rule: Test tree discovery
'''''''''''''''''''''''''

Background:


-  Given File "conftest.py" with content:

   .. code:: python

      from pytest_cuke import step

      @step('Passing step')
      def _():
        ...

Scenario: A feature next to tests is collected without a features directory


-  Given File "tests/local.feature" with content:

   .. code:: gherkin

      Feature: Local feature
        Scenario: Passes next to tests
          Given Passing step

-  When run pytest

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 1      |
   +--------+

Scenario: An explicit binding and autoload run each scenario once


-  Given File "cases/bound.feature" with content:

   .. code:: gherkin

      Feature: Bound feature
        Scenario: Bound scenario
          Given Passing step
        Scenario: Autoload scenario
          Given Passing step

-  Given File "tests/test_bound.py" with content:

   .. code:: python

      from pytest_cuke import scenarios

      test_bound = scenarios("cases/bound.feature", filter_="Bound scenario")

-  When run pytest

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 2      |
   +--------+
