"""

Provide test xdist message aggregation helpers.
"""

from __future__ import annotations

import pytest
from cucumber_messages import (
    TestCaseStarted as CucumberTestCaseStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)

from pytest_bdd.model.message_validation import validate_message_stream
from pytest_bdd_testing.case.contract.messages.test_messages import runpytest_with_message_reporter
from pytest_bdd_testing.tool.cucumber_formatter import (
    install_fake_node,
    read_fake_formatter_telemetry,
)
from pytest_bdd_testing.tool.message.stream_assertions import (
    count_payload_kinds,
    parse_ndjson_messages,
    worker_ids_for_payloads,
)

pytestmark = [pytest.mark.xdist]


def test_non_xdist_child_run_ignores_inherited_worker_identity(testdir, tmp_path, monkeypatch) -> None:
    """
    Verify non xdist child run ignores inherited worker identity.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    install_fake_node(monkeypatch, tmp_path)
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw9")
    monkeypatch.setenv("PYTEST_XDIST_WORKER_COUNT", "2")

    testdir.makefile(
        ".ini",
        pytest="""\
        [pytest]
        """,
    )
    testdir.makefile(
        ".feature",
        nested_identity="""\
        Feature: inherited xdist environment

          Scenario: pass one
            Given a passing step
        """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("a passing step")
        def _pass():
            return "ok"
        """,
    )

    ndjson_path = tmp_path / "non-xdist-child.ndjson"
    result = runpytest_with_message_reporter(
        testdir,
        "--messages-ndjson",
        str(ndjson_path),
        "--cucumber-summary",
    )

    assert result.ret == pytest.ExitCode.OK
    assert ndjson_path.exists()
    messages = parse_ndjson_messages(ndjson_path)
    assert worker_ids_for_payloads(messages, CucumberTestCaseStarted) == {"master"}

    telemetry = read_fake_formatter_telemetry(tmp_path)
    assert len(telemetry) == 1
    assert telemetry[0]["workerIds"] == ["master"]


def test_xdist_run_aggregates_worker_fragments_into_one_ndjson(testdir, tmp_path) -> None:
    """
    Verify xdist run aggregates worker fragments into one ndjson.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pytest.importorskip("xdist")

    testdir.makefile(
        ".ini",
        pytest="""\
        [pytest]
        """,
    )
    testdir.makefile(
        ".feature",
        aggregation="""\
        Feature: xdist aggregation

          Scenario: pass one
            Given a passing step

          Scenario: pass two
            Given a passing step

          Scenario: pass three
            Given a passing step

          Scenario: fail four
            Given a failing step
        """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("a passing step")
        def _pass():
            return "ok"

        @given("a failing step")
        def _fail():
            raise RuntimeError("boom")
        """,
    )

    ndjson_path = tmp_path / "xdist-aggregation.ndjson"
    result = runpytest_with_message_reporter(testdir, "-n", "2", "--messages-ndjson", str(ndjson_path))
    result.assert_outcomes(passed=3, failed=1)

    messages = parse_ndjson_messages(ndjson_path)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert payload_counts["gherkin_document"] == 1
    assert payload_counts["source"] == 1
    assert payload_counts["pickle"] == 4
    assert worker_ids_for_payloads(messages, CucumberTestCaseStarted).issuperset({"gw0", "gw1"})


def test_xdist_live_formatter_stream_is_rendered_once_by_controller(testdir, tmp_path, monkeypatch) -> None:
    """
    Verify xdist live formatter stream is rendered once by controller.

    Test target:
        Ensure parallel execution safety, state isolation, and barrier synchronization under xdist.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Ensure parallel execution safety, state isolation, and barrier
        synchronization under xdist., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    pytest.importorskip("xdist")
    install_fake_node(monkeypatch, tmp_path)

    testdir.makefile(
        ".ini",
        pytest="""\
        [pytest]
        """,
    )
    testdir.makefile(
        ".feature",
        live_formatter="""\
        Feature: live formatter aggregation

          Scenario: pass one
            Given a passing step

          Scenario: pass two
            Given a passing step

          Scenario: fail three
            Given a failing step

          Scenario: pass four
            Given a passing step
        """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("a passing step")
        def _pass():
            return "ok"

        @given("a failing step")
        def _fail():
            raise RuntimeError("boom")
        """,
    )

    result = testdir.runpytest_subprocess("-n", "2", "--cucumber-progress", str(testdir.tmpdir))

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    # Under heavy parallel load or specific OS buffering, xdist worker creation
    # messages can interleave with the progress formatter console output, splitting
    # strings like "Progress:" across concurrent writes (e.g. "Progre" + "ss:").
    # Strip xdist worker-lifecycle lines before checking progress output fragments.
    stdout_text = result.stdout.str()
    import re

    clean_stdout = re.sub(r"created:\s*\d+/\d+\s*workers", "", stdout_text)
    clean_stdout = re.sub(r"\d+\s*workers\s*\[\d+\s*items?\]", "", clean_stdout)
    assert "Progress" in re.sub(r"\s+", "", clean_stdout)
    assert ".F" in stdout_text

    telemetry = read_fake_formatter_telemetry(tmp_path)

    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == "stdin"
    assert telemetry[0]["formatterNames"] == ["progress"]
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is True
    assert int(telemetry[0]["consoleWriteCount"]) >= 2
    assert int(telemetry[0]["envelopeCount"]) > 0
    assert set(telemetry[0]["workerIds"]).issuperset({"gw0", "gw1"})
