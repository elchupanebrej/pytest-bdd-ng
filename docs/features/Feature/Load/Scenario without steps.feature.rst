Feature: Invalid feature structure handling
'''''''''''''''''''''''''''''''''''''''''''

Invalid feature files should fail with a clear parse error.

Scenario: Report parse error when no scenario is defined
                                                        

-  Given File "test.feature" with content:

   .. code:: gherkin

      Given foo
      When bar
      Then baz

-  And File "test_cukes.py" with content:

   .. code:: python

      from pytest_bdd import scenarios

      test_cukes = scenarios('features')

-  When run pytest

-  Then pytest outcome must match lines:

   \| *FeatureConcreteParseError* \|
