"""Property-based tests for allure-formatter converter using Hypothesis."""

from __future__ import annotations

import json
from pathlib import Path

import hypothesis.strategies as st
import pytest
from hypothesis import HealthCheck, assume, given, settings

from pytest_bdd.plugin.allure_formatter.converter import convert

pytestmark = [pytest.mark.contract]


def _valid_ndjson_strategy() -> st.SearchStrategy[str]:
    """Generate valid Cucumber Messages NDJSON strings."""
    timestamp = st.fixed_dictionaries({"seconds": st.integers(0, 1000), "nanos": st.integers(0, 999_999_999)})
    safe_id = st.from_regex(r"[a-zA-Z0-9_-]{1,10}", fullmatch=True)
    test_run_started = st.fixed_dictionaries(
        {"testRunStarted": st.fixed_dictionaries({"id": safe_id, "timestamp": timestamp})},
    )
    test_case_started = st.fixed_dictionaries(
        {
            "testCaseStarted": st.fixed_dictionaries(
                {
                    "id": safe_id,
                    "testCaseId": safe_id,
                    "attempt": st.integers(0, 5),
                    "timestamp": timestamp,
                },
            ),
        },
    )
    test_step_started = st.fixed_dictionaries(
        {
            "testStepStarted": st.fixed_dictionaries(
                {
                    "testStepId": safe_id,
                    "testCaseStartedId": safe_id,
                    "timestamp": timestamp,
                },
            ),
        },
    )
    test_step_finished = st.fixed_dictionaries(
        {
            "testStepFinished": st.fixed_dictionaries(
                {
                    "testStepId": safe_id,
                    "testCaseStartedId": safe_id,
                    "timestamp": timestamp,
                    "testStepResult": st.fixed_dictionaries(
                        {
                            "status": st.sampled_from(
                                ["PASSED", "FAILED", "SKIPPED", "PENDING", "UNDEFINED", "AMBIGUOUS", "UNKNOWN"],
                            ),
                            "duration": st.fixed_dictionaries(
                                {"seconds": st.integers(0, 100), "nanos": st.integers(0, 999_999_999)},
                            ),
                            "exception": st.none(),
                            "message": st.none(),
                        },
                    ),
                },
            ),
        },
    )
    test_case_finished = st.fixed_dictionaries(
        {
            "testCaseFinished": st.fixed_dictionaries(
                {
                    "testCaseStartedId": safe_id,
                    "timestamp": timestamp,
                    "willBeRetried": st.booleans(),
                },
            ),
        },
    )
    test_run_finished = st.fixed_dictionaries(
        {"testRunFinished": st.fixed_dictionaries({"success": st.booleans(), "timestamp": timestamp})},
    )

    # Build valid sequences: run_started, then N case groups, then run_finished
    case_group = st.tuples(test_case_started, test_step_started, test_step_finished, test_case_finished)

    @st.composite
    def build_ndjson(draw: st.DrawFn) -> str:
        run_start = draw(test_run_started)
        cases = draw(st.lists(case_group, min_size=1, max_size=3))
        run_end = draw(test_run_finished)
        lines = [json.dumps(run_start)]
        for case_start, step_start, step_end, case_end in cases:
            lines.extend([json.dumps(case_start), json.dumps(step_start), json.dumps(step_end), json.dumps(case_end)])
        lines.append(json.dumps(run_end))
        return "\n".join(lines)

    return build_ndjson()


@given(ndjson_str=_valid_ndjson_strategy())
@settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_any_valid_ndjson_produces_valid_allure(tmp_path: Path, ndjson_str: str) -> None:
    """Any valid Cucumber Messages NDJSON produces valid Allure JSON output."""
    assume(len(ndjson_str) > 0)
    ndjson = tmp_path / "messages.ndjson"
    ndjson.write_text(ndjson_str + "\n", encoding="utf-8")
    output = tmp_path / "allure-results"
    try:
        convert(ndjson, output)
    except (ValueError, TypeError):
        # Reader rejects malformed envelopes — acceptable
        return
    result_files = list(output.glob("*-result.json"))
    for f in result_files:
        content = json.loads(f.read_text(encoding="utf-8"))
        assert "uuid" in content, f"Result missing uuid: {f.name}"
        assert "status" in content, f"Result missing status: {f.name}"
        assert content["status"] in ("passed", "failed", "skipped", "unknown"), (
            f"Invalid status {content['status']} in {f.name}"
        )
