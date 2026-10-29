Feature: Installed pytest-cuke explicit bindings
  An installed consumer can bind named feature scenarios through the canonical
  root-facade scenario and scenarios functions without autoload collection.

  Scenario Outline: Wheel and sdist execute both explicit root-facade bindings
    Given the pytest-cuke <distribution> built from this checkout is installed in a fresh consumer project
    And consumer file "features/explicit-bindings.feature" contains:
      """gherkin
      Feature: Explicit installed bindings
        Scenario: Bound with scenario
          Given the single scenario binding is selected

        Scenario: Bound with scenarios
          Given the plural scenarios binding is selected
      """
    And consumer file "test_explicit_bindings.py" contains:
      """python
      from pytest_cuke import given, scenario, scenarios


      @given("the single scenario binding is selected")
      def single_scenario_binding_is_selected() -> None:
          pass


      @given("the plural scenarios binding is selected")
      def plural_scenarios_binding_is_selected() -> None:
          pass


      @scenario("explicit-bindings.feature", "Bound with scenario")
      def test_single_scenario_binding() -> None:
          pass


      test_plural_scenarios_binding = scenarios(
          "explicit-bindings.feature", filter_="Bound with scenarios"
      )
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-json=explicit-report.json --color=no test_explicit_bindings.py"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "explicit-report.json" should report both explicitly bound scenarios

    Examples:
      | distribution |
      | wheel        |
      | sdist        |
