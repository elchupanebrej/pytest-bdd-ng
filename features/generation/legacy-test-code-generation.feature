Feature: Legacy test code generation
  Generated source remains valid when Gherkin adds conjunction step types.

  @e2e
  Scenario: Conjunctions and Unicode text produce valid Python bindings
    Given the pytest-cuke wheel built from this checkout is installed in a fresh step generation consumer project
    And consumer file "features/generated-source.feature" contains:
      """
      Feature: Generated source preserves Unicode ℼ
        Scenario: Quoted text survives generation
          Given a starting step
          And preserve Unicode ℼ and 𝑟 with "double" and 'single' quotes
      """
    And consumer file "tests/test_generated_source.py" contains:
      """python
      from pytest_cuke import scenario


      @scenario("generated-source.feature", "Quoted text survives generation")
      def test_generated_source():
          pass
      """
    When I run installed pytest from consumer directory "." with arguments "--rootdir=. --cuke-no-autoload --cuke-parser=python --cuke-generate --cuke-feature={consumer_path}/features/generated-source.feature -q tests/test_generated_source.py"
    Then pytest should exit with code 0
    And pytest output should include "@step('preserve Unicode ℼ and 𝑟 with"
