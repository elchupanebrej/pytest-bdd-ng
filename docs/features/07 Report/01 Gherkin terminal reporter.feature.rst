Feature: Gherkin terminal reporter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents human-readable terminal reporting for feature and
scenario execution outcomes.

Scenario: Verbose reporter shows feature and scenario names
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File "test.feature" with content:

  .. code:: gherkin

     Feature: Gherkin terminal output feature
       Scenario: Scenario example 1
         Given there is a bar
         When the bar is accessed
         Then world explodes

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import given, when, then

     @given("there is a bar")
     def _bar():
       return "bar"

     @when("the bar is accessed")
     def _accessed():
       pass

     @then("world explodes")
     def _explodes():
       pass

- When run pytest

  ======== =========================== ==
  cli_args --gherkin-terminal-reporter -v
  ======== =========================== ==
  ======== =========================== ==

- Then pytest outcome must contain tests with statuses:

  ====== ======
  passed failed
  ====== ======
  1      0
  ====== ======

- And pytest outcome must match lines:

  \| *Feature: Gherkin terminal output feature* \| \| *Scenario:
  Scenario example 1* \|

Scenario: Double-verbose mode renders substituted outline values
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File "test.feature" with content:

  .. code:: gherkin

     Feature: Gherkin terminal output feature
       Scenario Outline: Scenario example 2
         Given there are <start> cucumbers
         When I eat <eat> cucumbers
         Then I should have <left> cucumbers

         Examples:
         | start | eat | left |
         | 10    | 3   | 7    |

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import given, when, then, parsers

     @given(parsers.parse("there are {start} cucumbers"), target_fixture="start_cucumbers")
     def _start_cucumbers(start):
       return int(start)

     @when(parsers.parse("I eat {eat} cucumbers"))
     def _eat_cucumbers(start_cucumbers, eat):
       assert start_cucumbers > int(eat)

     @then(parsers.parse("I should have {left} cucumbers"))
     def _should_have(start_cucumbers, left):
       assert start_cucumbers == int(left) + 3

- When run pytest

  ======== =========================== ===
  cli_args --gherkin-terminal-reporter -vv
  ======== =========================== ===
  ======== =========================== ===

- Then pytest outcome must contain tests with statuses:

  ====== ======
  passed failed
  ====== ======
  1      0
  ====== ======

- And pytest outcome must match lines:

  \| *Scenario: Scenario example 2* \| \| *Given there are 10 cucumbers
  (PASSED)* \| \| *When I eat 3 cucumbers (PASSED)* \| \| *Then I should
  have 7 cucumbers (PASSED)* \|
