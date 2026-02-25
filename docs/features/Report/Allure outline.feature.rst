Feature: Allure outline reporting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents Allure reporting behavior for scenario outlines,
including plugin-gated execution when Allure integration is unavailable.

Scenario: Outline reporting is guarded by Allure availability
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Given Copy path from "features/Report/Allure/outline.feature" to test
   path "outline.feature"

-  And File "conftest.py" with content:

   .. code:: python

      from pytest_bdd import given

      @given("value one")
      @given("value two")
      def _value():
        pass

-  And File "test_sample.py" with content:

   .. code:: python

      import pytest
      from pytest_bdd import scenarios
      from pytest_bdd.compatibility.allure import ALLURE_INSTALLED

      pytestmark = [pytest.mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")]
      test = scenarios("outline.feature", "Scenario outline")

-  When run pytest

   ======== ==============
   cli_args -k test_sample
   ======== ==============
   ======== ==============

-  Then pytest outcome must contain tests with statuses:

   +---------+
   | skipped |
   +=========+
   | 1       |
   +---------+
