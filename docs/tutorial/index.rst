Tutorial for Behave/Cucumber users
==================================

.. _tutorial: https://thebddcoach.com/post/a-quick-introduction-to-pytest-bdd-ng-for-people-who-are-already-familiar-with-cucumber-or-behave/

Leslie's tutorial_ ...

Tutorial files
--------------

Feature definition:

.. literalinclude:: features/books.feature

Application source:

.. literalinclude:: src/catalog.py
   :language: python

Test bootstrap:

.. literalinclude:: tests/conftest.py
   :language: python

Desktop launcher:

.. literalinclude:: tests/books.desktop
   :language: text

Step definitions:

.. literalinclude:: tests/steps/library_steps.py
   :language: python


Set up the tutorial
-------------------

From the project root, activate a virtual environment and run:
``pip install -r docs/tutorial/requirements.txt``
