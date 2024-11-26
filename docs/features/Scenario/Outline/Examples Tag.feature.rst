Feature: Scenario Outline examples could be tagged
''''''''''''''''''''''''''''''''''''''''''''''''''

Rule:
     

Background:
           

-  Given File "steps.feature" with content:

   .. code:: gherkin

      Feature: Steps are executed by corresponding step keyword decorator

        Scenario Outline:
            Given I produce <outcome> test

            @passed
            Examples:
            |outcome|
            |passed |

            @failed
            Examples:
            |outcome|
            |failed |

            @both
            Examples:
            |outcome|
            |passed |
            |failed |

-  Given File "pytest.ini" with content:

   .. code:: ini

      [pytest]
      markers =
        passed
        failed
        both

-  And File "conftest.py" with content:

   .. code:: python

      from pytest_bdd.compatibility.pytest import fail
      from pytest_bdd import given

      @given('I produce passed test')
      def passing_step():
        ...

      @given('I produce failed test')
      def failing_step():
        fail('Enforce fail')

Scenario:
         

-  When run pytest

   ======== == ======
   cli_args -m passed
   ======== == ======
   ======== == ======

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      0
   ====== ======

.. _scenario-1:

Scenario:
         

-  When run pytest

   ======== == ======
   cli_args -m failed
   ======== == ======
   ======== == ======

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   0      1
   ====== ======

.. _scenario-2:

Scenario:
         

-  When run pytest

   ======== == ================
   cli_args -m passed or failed
   ======== == ================
   ======== == ================

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _scenario-3:

Scenario:
         

-  When run pytest

   ======== == ========
   cli_args -m not both
   ======== == ========
   ======== == ========

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _scenario-4:

Scenario:
         

-  When run pytest

   ======== == ====
   cli_args -m both
   ======== == ====
   ======== == ====

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _scenario-5:

Scenario:
         

-  When run pytest
-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   2      2
   ====== ======

Rule: Mixing tags on feature & examples level
                                             

.. _background-1:

Background:
           

-  Given File "steps.feature" with content:

   .. code:: gherkin

      @feature_tag
      Feature: Steps are executed by corresponding step keyword decorator
        Scenario Outline:
            Given I produce <outcome> test

            Examples:
            |outcome|
            |passed |

            @examples_tag
            Examples:
            |outcome|
            |failed |

-  Given File "pytest.ini" with content:

   .. code:: ini

      [pytest]
      markers =
        feature_tag
        examples_tag

-  And File "conftest.py" with content:

   .. code:: python

      from pytest_bdd.compatibility.pytest import fail
      from pytest_bdd import given

      @given('I produce passed test')
      def passing_step():
        ...

      @given('I produce failed test')
      def failing_step():
        fail('Enforce fail')

Example:
        

-  When run pytest

   ======== == ===========
   cli_args -m feature_tag
   ======== == ===========
   ======== == ===========

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      1
   ====== ======

.. _example-1:

Example:
        

-  When run pytest

   ======== == ============
   cli_args -m examples_tag
   ======== == ============
   ======== == ============

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   0      1
   ====== ======

.. _example-2:

Example:
        

-  When run pytest

   ======== == ===============
   cli_args -m not feature_tag
   ======== == ===============
   ======== == ===============

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   0      0
   ====== ======

.. _example-3:

Example:
        

-  When run pytest

   ======== == ================
   cli_args -m not examples_tag
   ======== == ================
   ======== == ================

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      0
   ====== ======

.. _example-4:

Example:
        

-  When run pytest

   ======== == =========== ==============
   cli_args -m feature_tag --collect-only
   ======== == =========== ==============
   ======== == =========== ==============

-  Then pytest outcome must match lines:

   +-------------------+
   | collected 2 items |
   +===================+
   +-------------------+

.. _example-5:

Example:
        

-  When run pytest

   ======== == ============ ==============
   cli_args -m examples_tag --collect-only
   ======== == ============ ==============
   ======== == ============ ==============

-  Then pytest outcome must match lines:

   +-----------------------------------------------+
   | collected 2 items / 1 deselected / 1 selected |
   +===============================================+
   +-----------------------------------------------+

.. _example-6:

Example:
        

-  When run pytest

   ======== == =============== ==============
   cli_args -m not feature_tag --collect-only
   ======== == =============== ==============
   ======== == =============== ==============

-  Then pytest outcome must match lines:

   +------------------------------------+
   | collected 2 items / 2 deselected\* |
   +====================================+
   +------------------------------------+

.. _example-7:

Example:
        

-  When run pytest

   ======== == ================ ==============
   cli_args -m not examples_tag --collect-only
   ======== == ================ ==============
   ======== == ================ ==============

-  Then pytest outcome must match lines:

   +-----------------------------------------------+
   | collected 2 items / 1 deselected / 1 selected |
   +===============================================+
   +-----------------------------------------------+
