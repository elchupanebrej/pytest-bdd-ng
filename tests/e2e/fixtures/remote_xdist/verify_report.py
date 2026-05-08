"""Provide verify report helpers."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream
from tests.messages.message_stream_assertions import count_payload_kinds, parse_ndjson_messages, worker_ids_for_payloads


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_path")
    parser.add_argument("verification_mode", nargs="?", default="success")
    parser.add_argument("transport_mode", nargs="?", default="socket")
    parser.add_argument("--min-console-writes", type=int, default=0)
    parser.add_argument("--expect-controller-only", action="store_true")
    return parser


def _load_fake_node_captures() -> list[dict[str, object]]:
    capture_dir = os.environ.get("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", "").strip()
    if not capture_dir:
        return []
    path = Path(capture_dir)
    if not path.exists():
        return []
    return [json.loads(capture_path.read_text(encoding="utf-8")) for capture_path in sorted(path.glob("*.json"))]


def main() -> int:
    """
    Run main.

    Raises:
        ValueError: If the operation cannot be completed.

    """
    options = _build_parser().parse_args()
    report_path = Path(options.report_path).resolve()
    verification_mode = options.verification_mode
    transport_mode = options.transport_mode
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
        msg = f"Unknown verification mode: {verification_mode}"
        raise ValueError(msg)

    captures = _load_fake_node_captures()
    if options.min_console_writes:
        assert captures, "expected fake node captures for console-write verification"
        console_write_count = sum(int(capture.get("consoleWriteCount", 0)) for capture in captures)
        assert console_write_count >= options.min_console_writes
    if options.expect_controller_only:
        assert len(captures) == 1, f"expected exactly one controller-owned formatter capture, got {len(captures)}"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
