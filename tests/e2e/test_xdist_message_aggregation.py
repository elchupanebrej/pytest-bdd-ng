from __future__ import annotations

import pytest
from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream
from tests.messages.message_stream_assertions import count_payload_kinds, parse_ndjson_messages, worker_ids_for_payloads
from tests.messages.test_messages import runpytest_with_message_reporter


def test_xdist_run_aggregates_worker_fragments_into_one_ndjson(testdir, tmp_path) -> None:
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
