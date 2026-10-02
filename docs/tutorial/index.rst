Tutorial for Behave/Cucumber users
==================================

.. _tutorial: https://thebddcoach.com/post/a-quick-introduction-to-pytest-bdd-ng-for-people-who-are-already-familiar-with-cucumber-or-behave/

Leslie's tutorial_ ...

The runnable project lives in ``examples/tutorial``. Pytest discovers its
feature file automatically, without a mirror test module.

Feature
-------

.. literalinclude:: ../../examples/tutorial/features/books.feature
   :language: gherkin

Step definitions
----------------

.. literalinclude:: ../../examples/tutorial/tests/steps/library_steps.py
   :language: python


Set up the tutorial
-------------------

From ``examples/tutorial``, activate a virtual environment and run:
``pip install -r requirements.txt``
Then run ``python -m pytest`` from the same directory.
