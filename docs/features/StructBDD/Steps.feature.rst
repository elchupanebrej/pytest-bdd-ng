Feature: StructBDD step execution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This feature documents StructBDD step registration and execution
behavior in end-to-end scenario runs.

Scenario: Execute steps from StructBDD YAML definition
''''''''''''''''''''''''''''''''''''''''''''''''''''''

-  Given File "steps.bdd.yaml" with content:

   .. code:: yaml

      Name: Steps are executed one by one
      Steps:
        - Step:
            Name: Executed step by step
            Steps:
              - Given: I have a foo fixture with value "foo"
              - And: there is a list
              - When: I append 1 to the list
              - And: I append 2 to the list
              - And: I append 3 to the list
              - Then: foo should have value "foo"
              - But: the list should be [1, 2, 3]

-  And File "conftest.py" with content:

   .. code:: python

      from pytest_bdd import step, given, when, then, scenario

      @scenario("steps.bdd.yaml", "Executed step by step")
      def test_steps():
        pass

      @step('I have a foo fixture with value "foo"', target_fixture="foo", liberal=True)
      def _foo():
        return "foo"

      @given("there is a list", target_fixture="results", liberal=True)
      def _results():
        return []

      @when("I append 1 to the list")
      def _append_1(results):
        results.append(1)

      @when("I append 2 to the list")
      def _append_2(results):
        results.append(2)

      @when("I append 3 to the list")
      def _append_3(results):
        results.append(3)

      @then('foo should have value "foo"')
      def _foo_is_foo(foo):
        assert foo == "foo"

      @then("the list should be [1, 2, 3]")
      def _check_results(results):
        assert results == [1, 2, 3]

-  When run pytest

-  Then pytest outcome must contain tests with statuses:

   ====== ======
   passed failed
   ====== ======
   1      0
   ====== ======
