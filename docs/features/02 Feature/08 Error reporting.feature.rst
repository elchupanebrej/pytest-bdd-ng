Feature: Error reporting for invalid feature files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Users should get a clear parser error when a single feature file
incorrectly contains more than one ``Feature:`` declaration. This
protects against ambiguous parsing and explains the expected failure
mode.

Scenario: Reject multiple Feature declarations in one file
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

- Given File "wrong.feature" with content:

  .. code:: gherkin

     Feature: Feature One

       Background:
         Given I have A
         And I have B

       Scenario: Do something with A
         When I do something with A
         Then something about B

     Feature: Feature Two

       Background:
         Given I have A

       Scenario: Something that just needs A
         When I do something else with A
         Then something else about B

       Scenario: Something that needs B again
         Given I have B
         When I do something else with B
         Then something else about A and B

- When run pytest

- Then pytest outcome must contain tests with statuses:

  +--------+
  | errors |
  +========+
  | 1      |
  +--------+

- And pytest outcome must match lines:

  \| *FeatureConcreteParseError:* \|
