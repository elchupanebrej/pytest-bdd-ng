from __future__ import annotations

import sys
from pathlib import Path

from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream
from tests.messages.message_stream_assertions import count_payload_kinds, parse_ndjson_messages, worker_ids_for_payloads


def main() -> int:
    report_path = Path(sys.argv[1]).resolve()
    verification_mode = sys.argv[2] if len(sys.argv) > 2 else "success"
    transport_mode = sys.argv[3] if len(sys.argv) > 3 else "socket"
    messages = parse_ndjson_messages(report_path)
    validation_result = validate_message_stream(messages, track_coverage=False)
    payload_counts = count_payload_kinds(messages)
    worker_ids = worker_ids_for_payloads(messages, CucumberTestCaseStarted)

    assert validation_result.status == "pass"
    assert payload_counts["meta"] == 1
    assert payload_counts["test_run_started"] == 1
    assert payload_counts["test_run_finished"] == 1
    assert transport_mode in {"socket", "via", "ssh"}
    if verification_mode == "success":
        assert len(worker_ids) >= 2
    elif verification_mode == "partial":
        assert len(worker_ids) == 1
    else:  # pragma: no cover - entrypoint contract guards valid modes
        raise ValueError(f"Unknown verification mode: {verification_mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
