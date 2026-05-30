Feature: Steps could have docstrings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Scenario: Read step doc string
''''''''''''''''''''''''''''''

- Given File "Steps.feature" with content:

  .. code:: gherkin

     Feature:
       Scenario:
         Given I check step docstring
           ```
           Step docstring
           ```

- And File "conftest.py" with content:

  .. code:: python

     from pytest_bdd import given

     @given('I check step docstring')
     def _(step):
       assert step.argument.doc_string.content == "Step docstring"

- When run pytest

- Then pytest outcome must contain tests with statuses:

  ====== ======
  passed failed
  ====== ======
  1      0
  ====== ======
