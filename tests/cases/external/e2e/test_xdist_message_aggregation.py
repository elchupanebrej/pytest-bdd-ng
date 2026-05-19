"""Provide test xdist message aggregation helpers."""

from __future__ import annotations

from glob import escape

import pytest
from contract.messages.message_stream_assertions import (
    count_payload_kinds,
    parse_ndjson_messages,
    worker_ids_for_payloads,
)
from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream
from pytest_bdd.testing.cucumber_formatters import (
    expected_formatter_visible_line,
    install_fake_node,
    read_fake_formatter_telemetry,
)
from tests.cases.contract.messages.test_messages import runpytest_with_message_reporter

pytestmark = [pytest.mark.xdist]


def test_non_xdist_child_run_ignores_inherited_worker_identity(testdir, tmp_path, monkeypatch) -> None:
    """Verify non xdist child run ignores inherited worker identity."""
    install_fake_node(monkeypatch, tmp_path)
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw9")
    monkeypatch.setenv("PYTEST_XDIST_WORKER_COUNT", "2")

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
    """Verify xdist run aggregates worker fragments into one ndjson."""
    pytest.importorskip("xdist")

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
    """Verify xdist live formatter stream is rendered once by controller."""
    pytest.importorskip("xdist")
    install_fake_node(monkeypatch, tmp_path)

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

    result = testdir.runpytest_subprocess("-n", "2", "--cucumber-progress")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines([f"*{escape(expected_formatter_visible_line('progress'))}*"])

    telemetry = read_fake_formatter_telemetry(tmp_path)

    assert len(telemetry) == 1
    assert telemetry[0]["sourceMode"] == "stdin"
    assert telemetry[0]["formatterNames"] == ["progress"]
    assert telemetry[0]["emittedVisibleOutputDuringStream"] is True
    assert int(telemetry[0]["consoleWriteCount"]) >= 2
    assert int(telemetry[0]["envelopeCount"]) > 0
    assert set(telemetry[0]["workerIds"]).issuperset({"gw0", "gw1"})
