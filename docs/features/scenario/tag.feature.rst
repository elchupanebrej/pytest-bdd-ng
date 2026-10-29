Feature: Scenarios could be tagged
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Background:
'''''''''''

-  Given File "steps.feature" with content:

   ::

      Feature: Steps are executed by corresponding step keyword decorator
        @passed
        Scenario: Passed
          Given I produce passed test

        @failed
        Scenario: Failed
          Given I produce failed test

        @both
        Rule:
          Scenario: Passed
            Given I produce passed test

          Scenario: Failed
            Given I produce failed test

-  Given File "pytest.ini" with content:

   ::

      [pytest]
      markers =
        passed
        failed
        both

-  And File "conftest.py" with content:

   ::

      from pytest_cuke.compatibility.pytest import fail
      from pytest_cuke import given

      @given('I produce passed test')
      def passing_step():
        ...

      @given('I produce failed test')
      def failing_step():
        fail('Enforce fail')

Scenario:
'''''''''

-  When I run pytest with arguments "-m passed"

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      0
   ====== ======

.. _scenario-1:

Scenario:
'''''''''

-  When I run pytest with arguments "-m failed"

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   0      1
   ====== ======

.. _scenario-2:

Scenario:
'''''''''

-  When I run pytest with arguments "-m 'passed or failed'"

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _scenario-3:

Scenario:
'''''''''

-  When I run pytest with arguments "-m 'not both'"

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _scenario-4:

Scenario:
'''''''''

-  When I run pytest with arguments "-m both"

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _scenario-5:

Scenario:
'''''''''

-  When run pytest
-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   2      2
   ====== ======
