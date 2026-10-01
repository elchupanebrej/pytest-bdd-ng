pytest-cuke
===========

`pytest-cuke` lets you write behavior-driven tests in Gherkin and run them
with pytest. Feature files describe behavior; Python step definitions use
pytest fixtures and assertions to exercise your application.

.. image:: https://img.shields.io/pypi/v/pytest-cuke.svg
   :target: https://pypi.org/project/pytest-cuke/
   :alt: PyPI
.. image:: https://readthedocs.org/projects/pytest-bdd-ng/badge/?version=default
   :target: https://pytest-bdd-ng.readthedocs.io/en/default/
   :alt: Documentation status
.. image:: https://badgen.net/badge/stand%20with/UKRAINE/?color=0057B8&labelColor=FFD700
   :target: https://savelife.in.ua/en/
   :alt: Stand with Ukraine

.. _pytest-bdd: https://github.com/pytest-dev/pytest-bdd

Quick start
-----------

Install the package in your project environment:

.. code-block:: console

   python -m pip install pytest-cuke

Add a feature file under your pytest test directory. Feature files are
collected automatically, so you do not need a Python wrapper for each file.

``tests/features/greeting.feature``:

.. code-block:: gherkin

   Feature: Greeting a visitor

     Scenario: Greet the visitor by name
       Given a visitor named Ada
       When the visitor is greeted
       Then the greeting is "Hello, Ada!"

Define the matching steps in ``tests/conftest.py``:

.. code-block:: python

   from pytest_cuke import given, then, when

   @given("a visitor named Ada", target_fixture="visitor")
   def visitor():
       return "Ada"

   @when("the visitor is greeted", target_fixture="greeting")
   def greet(visitor):
       return f"Hello, {visitor}!"

   @then('the greeting is "Hello, Ada!"')
   def check_greeting(greeting):
       assert greeting == "Hello, Ada!"

Run the example from the project root:

.. code-block:: console

   pytest -q tests

pytest discovers the feature, matches each step to its decorated Python
function, and reports the scenario as a normal pytest test. Step functions can
use pytest fixtures just like other tests.

Learn more
----------

* `Tutorial examples in the feature reference <https://pytest-bdd-ng.readthedocs.io/en/default/include.html#tutorial>`_
* `Detailed documentation and feature reference <https://pytest-bdd-ng.readthedocs.io/en/default/include.html>`_
* `Gherkin reference <https://cucumber.io/docs/gherkin/reference/>`_

How to contribute
-----------------

Please open an issue to discuss a change before submitting a pull request.
See the `compatibility matrix and migration audit <docs/compatibility-and-migration-audit.md>`_ for supported environments, prerequisites, and full acceptance proof
instructions.
