Feature: Step definition could use pytest fixtures as step parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Test setup is implemented within the Given section. Even though these
steps are executed imperatively to apply possible side-effects,
pytest-cuke is trying to benefit of the PyTest fixtures which is based
on the dependency injection and makes the setup more declarative style.

In pytest-cuke you just declare an argument of the step function that it
depends on and the PyTest will make sure to provide it.

Scenario:
'''''''''

-  Given File "conftest.py" with content:

   ::

      from pytest import fixture
      from pytest_cuke import given, when, then

      @fixture
      def pocket():
        yield [{"cherry": "delicious"}]

      @given("I have an old pickle", param_defaults={"age": "old"}, target_fixture='pickle_age', params_fixtures_mapping=False)
      def i_have_cucumber(pocket):
          pocket.append({"age": "old", "cucumber": "pickle"})

      @when("I check pocket I found cucumber there")
      def i_check_pocket_for_cucumber(pocket):
        assert any(filter(lambda item: "cucumber" in item.keys(), pocket))

      @then("I lost everything")
      def i_check_pocket_for_cucumber(pocket):
        while pocket:
          pocket.pop()

-  Given File "Cucumber.feature" with content:

   ::

      Feature:
        Scenario:
          Given I have an old pickle
          When I check pocket I found cucumber there
          Then I lost everything

-  Given File "test_freshness.py" with content:

   ::

      from pytest_cuke import scenario

      @scenario("Cucumber.feature")
      def test_passing_feature(pocket):
        assert not pocket

-  When I run pytest with arguments "--cuke-no-autoload"

-  Then pytest outcome must contain tests with statuses:

   +--------+
   | passed |
   +========+
   | 1      |
   +--------+
