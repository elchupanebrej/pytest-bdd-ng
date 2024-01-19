Features by example
!!!!!!!!!!!!!!!!!!!

The following examples illustrate various ways of using feature files in gherkin to describe behavior.


.. NOTE:: Features below are part of end-to-end test suite; You always could find most specific
          use cases of **pytest-bdd-ng** by investigation of its regression
          test suite https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/tests

Tutorial launch.feature
!!!!!!!!!!!!!!!!!!!!!!!

For the purpose of the tutorial, this simple example illustrates the launch of a minimal feature test.
Think of this as a minimal example of BDD.

.. include:: ../Features/Tutorial launch.feature
   :code: gherkin

Gherkin feature launch by pytest.feature
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This is a more sophisticated example to illustrate the test of a real feature of pytest.
Think of this as an example of pytest invoking tests written in ``gherkin``

.. include:: ../Features/Gherkin feature launch by pytest.feature
   :code: gherkin

Tags for Scenario Outlines examples.feature
###########################################

This example illustrates a more specific use of tags. Think of this example as a way to show permutations of a particular feature within ``gherkin``.


.. include:: ../Features/Scenario/Outline/Tags for Scenario Outlines examples.feature
   :code: gherkin
