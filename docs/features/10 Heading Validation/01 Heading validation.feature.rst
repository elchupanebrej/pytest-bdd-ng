Feature: Heading validation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Feature and Scenario names must be provided in valid .feature.md files.

Scenario: Empty feature heading is detected
'''''''''''''''''''''''''''''''''''''''''''

- Given Feature file has empty heading
- When run heading validation
- Then Heading validation reports EMPTY_HEADING_TITLE_CODE

Scenario: Empty scenario heading is detected
''''''''''''''''''''''''''''''''''''''''''''

- Given Feature file has empty scenario heading
- When run heading validation
- Then Heading validation reports EMPTY_HEADING_TITLE_CODE

Scenario: Valid headings pass validation
''''''''''''''''''''''''''''''''''''''''

- Given File "valid.feature.md" with content:

  .. code:: markdown

     # Feature: Valid feature heading
     ## Scenario: Valid scenario heading
     * Given a valid step

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import given
     @given("a valid step")
     def _pass():
         pass

- And File "test_valid.py" with content:

  .. code:: python

     from pytest_bdd import scenarios
     scenarios("valid.feature.md")

- When run pytest \| cli_args \| -k \| valid.feature.md \|
- Then pytest outcome must contain tests with statuses: \| passed \|
  \|--------\| \| 1 \|
