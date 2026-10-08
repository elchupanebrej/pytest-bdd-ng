Feature: Cucumber Messages reporting spine
  Real autoload runs validate each envelope before delivering the same ordered stream
  to configured output and consumer extension sinks.

  Scenario: A runtime stream fans out truthful outcomes and a terminal event
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs reporting-spine probe "runtime-outcomes"
    And consumer file "features/reporting-outcomes.feature" contains:
      """gherkin
      Feature: Reporting spine runtime outcomes
        Scenario: A reporting spine step passes
          Given the reporting spine step passes

        Scenario: A reporting spine step fails
          Given the reporting spine step fails

        Scenario: A reporting spine step skips
          Given the reporting spine step skips

        Scenario: An undefined reporting spine step stays undefined
          Given this reporting spine step has no definition
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And consumer reporting-spine artifacts "messages.ndjson" and "messages.validated.ndjson" should preserve outcome terminal events with protocol "28.0.0"

  Scenario: A pytest teardown failure keeps the step passed and the run unsuccessful
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs reporting-spine probe "teardown-failure"
    And consumer file "features/teardown-failure.feature" contains:
      """gherkin
      Feature: Reporting spine teardown failure
        Scenario: A step passes before pytest teardown fails
          Given the reporting spine step passes before pytest teardown
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And pytest output should contain "reporting spine teardown failure sentinel"
    And consumer reporting-spine artifacts "messages.ndjson" and "messages.validated.ndjson" should keep the passed step and failed run after teardown failure

  Scenario: An external tryfirst session-finish failure marks the Messages run unsuccessful
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest_cuke import given


      @given("the external session-finish scenario passes")
      def external_session_finish_scenario_passes():
          pass


      @pytest.hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_sessionfinish(session, exitstatus):
          outcome = yield
          raise RuntimeError("external tryfirst pytest_sessionfinish failure sentinel")
      """
    And consumer file "features/external-session-finish-failure.feature" contains:
      """gherkin
      Feature: External session-finish failure
        Scenario: The step passes before session finish fails
          Given the external session-finish scenario passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And pytest output should contain "external tryfirst pytest_sessionfinish failure sentinel"
    And consumer Messages artifact "messages.ndjson" should record the failed terminal run and AFTER_TEST_RUN diagnostic after an external tryfirst session-finish failure

  Scenario: A late-registered tryfirst session-finish failure appears in Messages
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest_cuke import given


      @given("the xdist reporting spine step passes")
      def xdist_reporting_spine_step_passes():
          pass


      class LateExternalSessionFinish:
          @pytest.hookimpl(hookwrapper=True, tryfirst=True)
          def pytest_sessionfinish(self, session, exitstatus):
              yield
              raise RuntimeError("external tryfirst pytest_sessionfinish failure sentinel")


      @pytest.hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_sessionstart(session):
          yield
          session.config.pluginmanager.register(LateExternalSessionFinish(), "late-external-session-finish")
      """
    And consumer file "features/late-external-session-finish-failure.feature" contains:
      """gherkin
      Feature: Late external session-finish failure
        Scenario: The step passes before session finish fails
          Given the xdist reporting spine step passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-parser=python -n2 --dist=load --max-worker-restart=0 --color=no -q features/late-external-session-finish-failure.feature"
    Then pytest should exit with code 1
    And pytest output should contain "external tryfirst pytest_sessionfinish failure sentinel"
    And consumer output and Messages artifact "messages.ndjson" should exclude xdist diagnostics "missing_worker_manifest,partial_stream"
    And consumer Messages artifact "messages.ndjson" should report a failed root AFTER_TEST_RUN hook with sentinel "external tryfirst pytest_sessionfinish failure sentinel", a passed worker step, and an unsuccessful root run

  Scenario: Before and after session hooks emit linked Cucumber Messages events
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs reporting-spine run-hook probe "failing-after-hook"
    And consumer file "features/run-hook-lifecycle.feature" contains:
      """gherkin
      Feature: Reporting spine run-hook lifecycle
        Scenario: The test case runs between session hooks
          Given the reporting spine run-hook step passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And pytest output should contain "reporting spine after-session hook sentinel"
    And consumer reporting-spine artifacts "messages.ndjson" and "messages.validated.ndjson" should preserve the ordered before and failed after run-hook lifecycle for protocol "28.0.0"

  Scenario: A trylast session-finish hook stays failed under xdist
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest_cuke import given


      @given("the xdist reporting spine step passes")
      def xdist_reporting_spine_step_passes():
          pass


      @pytest.hookimpl(hookwrapper=True, trylast=True)
      def pytest_sessionfinish(session, exitstatus):
          outcome = yield
          outcome.force_exception(RuntimeError("xdist reporting spine after-session hook sentinel"))
    """
    And consumer file "features/xdist-run-hook.feature" contains:
      """gherkin
      Feature: Reporting spine xdist hook lifecycle
        Scenario: A scenario passes before session finish fails
          Given the xdist reporting spine step passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-parser=python -n2 --max-worker-restart=0 --color=no -q features/xdist-run-hook.feature"
    Then pytest output should contain "xdist reporting spine after-session hook sentinel"
    And consumer Messages artifact "messages.ndjson" should report a failed root AFTER_TEST_RUN hook with sentinel "xdist reporting spine after-session hook sentinel", a passed worker step, and an unsuccessful root run

  Scenario: A tryfirst session-finish failure marks the root Messages run unsuccessful under xdist
    Given the pytest-cuke wheel with pytest-xdist is installed in a fresh test-group consumer
    And consumer file "conftest.py" contains:
      """python
      import pytest
      from pytest_cuke import given


      @given("the xdist reporting spine step passes")
      def xdist_reporting_spine_step_passes():
          pass


      @pytest.hookimpl(hookwrapper=True, tryfirst=True)
      def pytest_sessionfinish(session, exitstatus):
          outcome = yield
          raise RuntimeError("xdist external tryfirst session-finish failure sentinel")
      """
    And consumer file "features/xdist-tryfirst-run-hook.feature" contains:
      """gherkin
      Feature: External xdist session-finish failure
        Scenario: The step passes before an external session-finish failure
          Given the xdist reporting spine step passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson --cuke-parser=python -n2 --dist=load --max-worker-restart=0 --color=no -q features/xdist-tryfirst-run-hook.feature"
    Then pytest should exit with code 1
    And pytest output should contain "xdist external tryfirst session-finish failure sentinel"
    And consumer output and Messages artifact "messages.ndjson" should exclude xdist diagnostics "missing_worker_manifest,partial_stream"
    And consumer Messages artifact "messages.ndjson" should report a failed root AFTER_TEST_RUN hook with sentinel "xdist external tryfirst session-finish failure sentinel", a passed worker step, and an unsuccessful root run

  Scenario: A multi-payload extension event is rejected before either sink
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And an installed consumer extension submits a "multi-payload" envelope through pytest_cuke_message
    And consumer file "test_reporting_spine.py" contains:
      """python
      def test_reporting_spine_probe():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-messages-ndjson=messages.ndjson -q test_reporting_spine.py"
    Then pytest should exit with code 1
    And the consumer should report one structured message diagnostic "INVALID_PAYLOAD_SHAPE" at position 7 with payload kind "null"
    And consumer Messages artifact "messages.ndjson" should retain the valid terminal reporting spine around the rejected "multi-payload" event

  Scenario: A schema-invalid extension event is rejected before either sink
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And an installed consumer extension submits a "schema-invalid" envelope through pytest_cuke_message
    And consumer file "test_reporting_spine.py" contains:
      """python
      def test_reporting_spine_probe():
          pass
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-no-autoload --cuke-messages-ndjson=messages.ndjson -q test_reporting_spine.py"
    Then pytest should exit with code 1
    And the consumer should report one structured message diagnostic "SCHEMA_VALIDATION_ERROR" at position 7 with payload kind "test_run_started"
    And consumer Messages artifact "messages.ndjson" should retain the valid terminal reporting spine around the rejected "schema-invalid" event

  Scenario: A duplicate lifecycle ID from the extension seam is rejected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And an installed consumer extension submits a "duplicate-lifecycle-id" envelope through pytest_cuke_message
    And consumer file "features/reporting-spine-probe.feature" contains:
      """gherkin
      Feature: Reporting spine extension probe
        Scenario: The extension probe runs
          Given the reporting spine probe passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And the consumer should report one structured message diagnostic "DUPLICATE_LIFECYCLE_ID" with payload kind "test_case_started"
    And consumer Messages artifact "messages.ndjson" should retain the valid terminal reporting spine around the rejected "duplicate-lifecycle-id" event

  Scenario: An orphan extension reference is rejected
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And an installed consumer extension submits an "orphan-reference" envelope through pytest_cuke_message
    And consumer file "features/reporting-spine-probe.feature" contains:
      """gherkin
      Feature: Reporting spine extension probe
        Scenario: The extension probe runs
          Given the reporting spine probe passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And the consumer should report one structured message diagnostic "ORPHAN_REFERENCE" with payload kind "attachment"
    And consumer Messages artifact "messages.ndjson" should retain the valid terminal reporting spine around the rejected "orphan-reference" event

  Scenario: An out-of-order run hook is rejected while the real terminal event closes the stream
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And an installed consumer extension submits an "out-of-order-lifecycle" envelope through pytest_cuke_message
    And consumer file "features/reporting-spine-probe.feature" contains:
      """gherkin
      Feature: Reporting spine extension probe
        Scenario: The extension probe runs
          Given the reporting spine probe passes
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 1
    And the late lifecycle probe should capture one structured message diagnostic "OUT_OF_ORDER_LIFECYCLE" with payload kind "test_run_hook_started"
    And consumer Messages artifact "messages.ndjson" should retain the valid terminal reporting spine around the rejected "out-of-order-lifecycle" event

  Scenario: Two sequential pytest sessions in one process keep validated sinks and IDs isolated
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer installs reporting-spine probe "passing-session"
    And consumer file "features/repeated-session.feature" contains:
      """gherkin
      Feature: Repeated reporting spine session
        Scenario: The current session passes
          Given the reporting spine step passes
      """
    When I run installed pytest twice in one process with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=first-session.ndjson -q" and then "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=second-session.ndjson -q"
    Then consumer repeated pytest sessions should exit with codes "0,0"
    And consumer reporting-spine sessions "first-session.ndjson" and "second-session.ndjson" should have isolated validated sinks and lifecycle IDs

  Scenario: Reporting stays disabled without Allure or Node installed
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the installed consumer has no Allure Python adapters or Node on PATH
    And consumer file "conftest.py" contains:
      """python
      from pytest_cuke import given


      @given("reporting stays disabled")
      def reporting_stays_disabled():
          pass
      """
    And consumer file "features/reporting-off.feature" contains:
      """gherkin
      Feature: Reporting off
        Scenario: Reporting remains optional
          Given reporting stays disabled
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features -q"
    Then pytest should exit with code 0
    And pytest output should include "1 passed"
    And the consumer file "messages.ndjson" should not exist
    And the consumer file "validated-messages.ndjson" should not exist
    And the consumer file "report.json" should not exist
