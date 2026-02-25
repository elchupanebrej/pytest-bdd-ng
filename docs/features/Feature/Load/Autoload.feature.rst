Feature: Gherkin features autoload
''''''''''''''''''''''''''''''''''

By default Gherkin features in the test hierarchy are collected as
pytest tests. This feature documents how to disable autoload while still
running explicitly bound scenarios.

Rule: Feature autoload
                      

Background:
           

-  Given File "Passing.feature" with content:

   .. code:: gherkin

      Feature: Passing feature
        Scenario: Passing scenario
          * Passing step

-  Given File "Another.passing.feature.md" with content:

   .. code:: markdown

      # Feature: Passing feature
      ## Scenario: Passing scenario
      * Given Passing step

-  Given File "conftest.py" with content:

   .. code:: python

      from pytest_bdd import step

      @step('Passing step')

      def _():
        ...

Scenario: Feature is loaded by default
                                      

-  When run pytest

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 2      |
   +--------+

Scenario: Feature autoload could be disabled via command line
                                                             

-  When run pytest

   ======== ==========================
   cli_args --disable-feature-autoload
   ======== ==========================
   ======== ==========================

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 0      |
   +--------+

.. _scenario-feature-autoload-could-be-disabled-via-pytestini:

Scenario: Feature autoload could be disabled via pytest.ini
                                                           

-  Given Set pytest.ini content to:

   .. code:: ini

      [pytest]
      disable_feature_autoload=true

-  When run pytest

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 0      |
   +--------+

Scenario: Explicit scenario binding still runs when autoload is disabled
                                                                        

-  Given File "test_explicit.py" with content:

   .. code:: python

      from pytest_bdd import scenario

      @scenario("Passing.feature", "Passing scenario")
      def test_explicit():
        pass

-  When run pytest

   ======== ==========================
   cli_args --disable-feature-autoload
   ======== ==========================
   ======== ==========================

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 1      |
   +--------+
