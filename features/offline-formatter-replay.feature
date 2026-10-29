Feature: Standalone formatter rendering from saved Messages
  The cuke command renders a saved Cucumber Messages stream without collecting
  tests or running pytest fixtures.

  Scenario: Saved Messages render to multiple outputs after test sources are removed
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And the consumer installs the pinned Cucumber pretty formatter packages
    And the consumer registers an official Cucumber PrettyPrinter replay formatter
    And consumer file "conftest.py" contains:
      """python
      import sys
      from pathlib import Path

      import pytest
      from pytest_cuke import given
      from pytest_cuke.formatter_api import FormatterRequest


      ROOT = Path(__file__).parent
      (ROOT / "conftest-imported.marker").write_text("imported", encoding="utf-8")


      @pytest.fixture(autouse=True)
      def trap_fixture():
          (ROOT / "fixture-executed.marker").write_text("executed", encoding="utf-8")


      @given("the saved Messages scenario step passes")
      def saved_messages_scenario_step_passes():
          (ROOT / "feature-step-executed.marker").write_text("executed", encoding="utf-8")


      def pytest_cuke_formatter_requests(config):
          del config
          command = (sys.executable, str(ROOT / "formatter_probe.py"))
          return (
              FormatterRequest(
                  name="probe",
                  command=command,
                  output_path=ROOT / "live-probe.ndjson",
                  working_directory=ROOT,
                  timeout_seconds=5.0,
              ),
              FormatterRequest(
                  name="probe-copy",
                  command=command,
                  output_path=ROOT / "live-probe-copy.ndjson",
                  working_directory=ROOT,
                  timeout_seconds=5.0,
              ),
          )
      """
    And consumer file "features/trapped-saved-run.feature" contains:
      """gherkin
      Feature: Trapped saved run
        Scenario: One real scenario is recorded before its sources are removed
          Given the saved Messages scenario step passes
      """
    And consumer file "test_trap.py" contains:
      """python
      from pathlib import Path


      ROOT = Path(__file__).parent
      (ROOT / "test-source-imported.marker").write_text("imported", encoding="utf-8")


      def test_trap_source_runs_during_the_live_pytest_session():
          (ROOT / "test-body-executed.marker").write_text("executed", encoding="utf-8")
      """
    When I run installed pytest with arguments "--rootdir=. --cuke-autoload --cuke-features-dir=features --cuke-messages-ndjson=messages.ndjson -q"
    Then pytest should exit with code 0
    And consumer Messages artifact "messages.ndjson" should capture a successful live run with the trap sources
    When I remove consumer file "conftest.py"
    And I remove consumer file "test_trap.py"
    And I remove consumer file "features/trapped-saved-run.feature"
    And I clear the consumer trap source markers
    When I run command "cuke" with arguments "replay messages.ndjson --formatter probe=rendered-one.ndjson --formatter probe-copy=rendered-two.ndjson --formatter official-pretty=pretty-replay.txt"
    Then the command should exit with code 0
    And consumer replay artifacts "rendered-one.ndjson" and "rendered-two.ndjson" should match both live formatter outputs
    And consumer replay artifact "pretty-replay.txt" should match the pinned official Cucumber formatter output
    And consumer Messages artifact "messages.ndjson" should remain byte-identical to the captured saved stream
    And standalone Messages rendering should not import conftest or run test fixtures
    When I run command "cuke" with arguments "replay messages.ndjson --formatter probe=rendered-one-again.ndjson --formatter probe-copy=rendered-two-again.ndjson"
    Then the command should exit with code 0
    And consumer replay artifacts "rendered-one-again.ndjson" and "rendered-two-again.ndjson" should match the first replay byte for byte
    And consumer Messages artifact "messages.ndjson" should remain byte-identical to the captured saved stream
    When I run command "cuke" with arguments "replay messages.ndjson --formatter probe=shared.ndjson --formatter probe-copy=shared.ndjson"
    Then the command should exit with a non-zero code
    And the replay output conflict should name formatters "probe" and "probe-copy" and destination "shared.ndjson"

  Scenario: A missing Messages file produces a path-specific error
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    When I run command "pytest-cuke" with arguments "replay missing-messages.ndjson --formatter probe=missing-output.ndjson"
    Then the command should exit with a non-zero code
    And the missing saved Messages diagnostic should name "missing-messages.ndjson"
    And consumer artifact "missing-output.ndjson" should not be published by replay

  Scenario Outline: Invalid Messages identify the input path, line, and error
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And consumer Messages file "malformed-messages.ndjson" contains malformed case "<malformed_case>"
    When I run command "cuke" with arguments "replay malformed-messages.ndjson --formatter probe=malformed-output.ndjson"
    Then the command should exit with a non-zero code
    And the malformed saved Messages diagnostic should identify "malformed-messages.ndjson" at line <error_line> with error "<expected_error>"
    And consumer artifact "malformed-output.ndjson" should not be published by replay

    Examples:
      | malformed_case  | error_line | expected_error            |
      | invalid-json    | 2          | invalid Messages JSON     |
      | invalid-envelope| 2          | expected a JSON object    |
      | invalid-schema  | 2          | SCHEMA_VALIDATION_ERROR   |
      | orphan-reference| 3          | ORPHAN_REFERENCE          |

  Scenario: A missing output parent is reported before publishing an artifact
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And consumer Messages file "messages.ndjson" contains a valid saved run
    When I run command "cuke" with arguments "replay messages.ndjson --formatter probe=missing-parent/report.ndjson"
    Then the command should exit with a non-zero code
    And the replay output parent diagnostic should name "missing-parent"
    And consumer artifact "missing-parent/report.ndjson" should not be published by replay

  Scenario: Two selected terminal formatters produce a conflict diagnostic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And consumer Messages file "messages.ndjson" contains a valid saved run
    When I run command "cuke" with arguments "replay messages.ndjson --formatter probe=- --formatter probe-copy=-"
    Then the command should exit with a non-zero code
    And the replay terminal conflict should name formatters "probe" and "probe-copy"

  Scenario: A formatter stderr and non-zero exit are reported without publishing output
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And the consumer registers a formatter that reports an error and exits with status 23
    And consumer Messages file "messages.ndjson" contains a valid saved run
    When I run command "cuke" with arguments "replay messages.ndjson --formatter probe-failure=failed-output.ndjson"
    Then the command should exit with a non-zero code
    And the replay formatter failure should report its stderr and exit status
    And consumer artifact "failed-output.ndjson" should not be published by replay

  Scenario: The official Node formatter reports a missing Node executable
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And the consumer installs the pinned Cucumber pretty formatter packages
    And the consumer registers an official Cucumber PrettyPrinter replay formatter
    And consumer Messages file "messages.ndjson" contains a valid saved run
    And the consumer removes Node.js from PATH
    When I run command "cuke" with arguments "replay messages.ndjson --formatter official-pretty=missing-node.txt"
    Then the command should exit with a non-zero code
    And the missing Node replay diagnostic should explain the requirement
    And consumer artifact "missing-node.txt" should not be published by replay

  Scenario: A missing npm package gives an installation diagnostic
    Given the pytest-cuke wheel built from this checkout is installed in a fresh consumer project
    And the consumer registers deterministic saved-stream formatter plugins "probe" and "probe-copy"
    And the consumer installs the pinned Cucumber pretty formatter packages
    And the consumer registers a formatter that requires a missing npm package
    And consumer Messages file "messages.ndjson" contains a valid saved run
    When I run command "cuke" with arguments "replay messages.ndjson --formatter missing-npm=missing-npm-output.ndjson"
    Then the command should exit with a non-zero code
    And the missing npm package replay diagnostic should be actionable
    And consumer artifact "missing-npm-output.ndjson" should not be published by replay
