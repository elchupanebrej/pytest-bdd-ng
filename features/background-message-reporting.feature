Feature: Cucumber Messages reporting for Background execution
  Installed autoloaded scenarios report expanded feature and Rule Background steps
  with stable step references and truthful lifecycle outcomes.

  Scenario: A feature Background and two-row Outline run with reporting disabled and enabled
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest import fixture
      from pytest_cuke import given, parsers, then, when


      @given(parsers.parse("the total starts at {total:d}"), target_fixture="total")
      def total_starts_at(total):
          return total


      @when(parsers.parse("I add {amount:d} credits"), target_fixture="total")
      def add_credits(total, amount):
          return total + amount


      @then(parsers.parse("the total is {expected:d}"))
      def total_is(total, expected):
          assert total == expected


      @given("the Background step fails")
      def background_step_fails():
          pytest.fail("background failure sentinel")


      @given("the remaining Background step must not run")
      def remaining_background_step_must_not_run():
          raise AssertionError("a step after the failing Background ran")


      @when("the scenario step after a failing Background must not run")
      def scenario_step_after_failing_background_must_not_run():
          raise AssertionError("a scenario step after the failing Background ran")


      @then("the final scenario step after a failing Background must not run")
      def final_scenario_step_after_failing_background_must_not_run():
          raise AssertionError("a final scenario step after the failing Background ran")


      @given("the Background requests a skip")
      def background_requests_skip():
          pytest.skip("background skip sentinel")


      @when("the scenario step after a skipped Background must not run")
      def scenario_step_after_skipped_background_must_not_run():
          raise AssertionError("a scenario step after a skipped Background ran")


      @fixture
      def broken_background_setup():
          raise RuntimeError("background setup failure sentinel")


      @given("the Background needs a fixture whose setup fails")
      def background_needs_broken_setup(broken_background_setup):
          pass


      @when("the scenario step after a setup failure must not run")
      def scenario_step_after_setup_failure_must_not_run():
          raise AssertionError("a scenario step after Background setup failure ran")
      """
    And consumer file "features/basic/feature-background.feature" contains:
      """gherkin
      Feature: Feature Background message reporting
        Background:
          Given the total starts at 10

        Scenario Outline: Adding <amount> credits updates the total
          When I add <amount> credits
          Then the total is <expected>

          Examples:
            | amount | expected |
            | 2      | 12       |
            | 7      | 17       |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/basic -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And the consumer file "messages.ndjson" should not exist
    And the consumer file "report.json" should not exist
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/basic --cuke-messages-ndjson=messages-only.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "messages-only.ndjson" should preserve the two-row feature Background step identities
    Given the consumer installs the pinned official Cucumber JSON runtime
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/basic --cuke-json=json-only.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "json-only.json" should report both Background rows as passed
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/basic --cuke-messages-ndjson=messages.ndjson --cuke-json=report.json -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "messages.ndjson" should preserve the two-row feature Background step identities
    And consumer artifacts "messages.ndjson" and "report.json" should agree on both successful Background rows

  Scenario: Feature and Rule Backgrounds with repeated text retain each expanded step identity
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given, parsers, then, when


      @given(parsers.parse("the total starts at {total:d}"), target_fixture="total")
      def total_starts_at(total):
          return total


      @when(parsers.parse("I add {amount:d} credits"), target_fixture="total")
      def add_credits(total, amount):
          return total + amount


      @then(parsers.parse("the total is {expected:d}"))
      def total_is(total, expected):
          assert total == expected
      """
    And consumer file "features/rule/rule-background.feature" contains:
      """gherkin
      Feature: Repeated Background step identities
        Background:
          Given the total starts at 10

        Rule: A rule can add another Background
          Background:
            Given the total starts at 10

          Scenario Outline: Repeated text remains distinct in each pickle
            Given the total starts at 10
            When I add <amount> credits
            Then the total is <expected>

            Examples:
              | amount | expected |
              | 2      | 12       |
              | 7      | 17       |
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/rule --cuke-messages-ndjson=rule-messages.ndjson -q"
    Then pytest should exit with code 0
    And the test outcome should have 2 passed scenarios
    And consumer artifact "rule-messages.ndjson" should preserve repeated feature and Rule Background step identities

  Scenario: Failed, skipped, and setup-failed Backgrounds close report lifecycles truthfully
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest import fixture
      from pytest_cuke import given, then, when


      @given("the Background step fails")
      def background_step_fails():
          pytest.fail("background failure sentinel")


      @given("the remaining Background step must not run")
      def remaining_background_step_must_not_run():
          raise AssertionError("a step after the failing Background ran")


      @when("the scenario step after a failing Background must not run")
      def scenario_step_after_failing_background_must_not_run():
          raise AssertionError("a scenario step after the failing Background ran")


      @then("the final scenario step after a failing Background must not run")
      def final_scenario_step_after_failing_background_must_not_run():
          raise AssertionError("a final scenario step after a failing Background ran")


      @given("the Background requests a skip")
      def background_requests_skip():
          pytest.skip("background skip sentinel")


      @when("the scenario step after a skipped Background must not run")
      def scenario_step_after_skipped_background_must_not_run():
          raise AssertionError("a scenario step after a skipped Background ran")


      @fixture
      def broken_background_setup():
          raise RuntimeError("background setup failure sentinel")


      @given("the Background needs a fixture whose setup fails")
      def background_needs_broken_setup(broken_background_setup):
          pass


      @when("the scenario step after a setup failure must not run")
      def scenario_step_after_setup_failure_must_not_run():
          raise AssertionError("a scenario step after Background setup failure ran")
      """
    And consumer file "features/failure/background-failure.feature" contains:
      """gherkin
      Feature: Failed Background lifecycle
        Background:
          Given the Background step fails
          And the remaining Background step must not run

        Scenario: Steps after a failed Background are skipped
          When the scenario step after a failing Background must not run
          Then the final scenario step after a failing Background must not run
      """
    And consumer file "features/skip/background-skip.feature" contains:
      """gherkin
      Feature: Skipped Background lifecycle
        Background:
          Given the Background requests a skip

        Scenario: A skipped Background skips scenario steps
          When the scenario step after a skipped Background must not run
      """
    And consumer file "features/setup/background-setup-failure.feature" contains:
      """gherkin
      Feature: Background setup failure lifecycle
        Background:
          Given the Background needs a fixture whose setup fails

        Scenario: A failed Background fixture closes the scenario lifecycle
          When the scenario step after a setup failure must not run
      """
    Given the consumer installs the pinned official Cucumber JSON runtime
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/failure --cuke-messages-ndjson=failure.ndjson --cuke-json=failure.json -q"
    Then pytest should exit with a non-zero code
    And consumer artifact "failure.ndjson" should close the Background lifecycle with statuses "failed, skipped, skipped, skipped" and an unsuccessful run
    And consumer artifact "failure.json" should report the Background failure and skipped steps
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/skip --cuke-messages-ndjson=skip.ndjson -q"
    Then pytest should exit with code 0
    And consumer artifact "skip.ndjson" should close the Background lifecycle with statuses "skipped, skipped" and a successful run
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features/setup --cuke-messages-ndjson=setup-failure.ndjson -q"
    Then pytest should exit with a non-zero code
    And consumer artifact "setup-failure.ndjson" should close the Background lifecycle with statuses "failed, skipped" and an unsuccessful run
