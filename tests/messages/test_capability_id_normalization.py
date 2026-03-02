from __future__ import annotations

from pytest_bdd.model.coverage.inventory import (
    canonical_capability_id,
    canonical_capability_key,
    canonical_payload_kind,
    parse_capability_id,
)


def test_canonical_payload_kind_converts_snake_case_to_camel_case() -> None:
    assert canonical_payload_kind("test_case_started") == "testCaseStarted"
    assert canonical_payload_kind("gherkin_document") == "gherkinDocument"


def test_canonical_payload_kind_preserves_existing_camel_case() -> None:
    assert canonical_payload_kind("testRunStarted") == "testRunStarted"


def test_canonical_capability_key_normalizes_payload_kind_only() -> None:
    assert canonical_capability_key("test_step_finished", "testStepResult.duration.nanos") == (
        "testStepFinished",
        "testStepResult.duration.nanos",
    )


def test_parse_and_canonical_capability_id() -> None:
    assert parse_capability_id("test_case_started.timestamp.seconds") == (
        "testCaseStarted",
        "timestamp.seconds",
    )
    assert canonical_capability_id("test_case_started.timestamp.seconds") == "testCaseStarted.timestamp.seconds"
