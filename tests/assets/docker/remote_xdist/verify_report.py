"""Provide verify report helpers."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from cucumber_messages import TestCaseStarted as CucumberTestCaseStarted  # type:ignore[attr-defined]

from pytest_bdd.model.message_validation import validate_message_stream
from tests.cases.contract.messages.message_stream_assertions import (
    count_payload_kinds,
    parse_ndjson_messages,
    worker_ids_for_payloads,
)

MIN_SUCCESS_WORKERS = 2


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

    Returns:
        Process exit code.

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

    require("message validation must pass", condition=validation_result.status == "pass")
    require("expected one meta message", condition=payload_counts["meta"] == 1)
    require("expected one test_run_started message", condition=payload_counts["test_run_started"] == 1)
    require("expected one test_run_finished message", condition=payload_counts["test_run_finished"] == 1)
    require(f"unexpected transport mode: {transport_mode}", condition=transport_mode in {"socket", "via", "ssh"})
    if verification_mode == "success":
        require("expected at least two worker ids", condition=len(worker_ids) >= MIN_SUCCESS_WORKERS)
    elif verification_mode == "partial":
        require("expected exactly one worker id", condition=len(worker_ids) == 1)
    else:  # pragma: no cover - entrypoint contract guards valid modes
        msg = f"Unknown verification mode: {verification_mode}"
        raise ValueError(msg)

    captures = _load_fake_node_captures()
    if options.min_console_writes:
        require("expected fake node captures for console-write verification", condition=bool(captures))
        console_write_count = sum(int(capture.get("consoleWriteCount", 0)) for capture in captures)
        require("too few console writes captured", condition=console_write_count >= options.min_console_writes)
    if options.expect_controller_only:
        require(
            f"expected exactly one controller-owned formatter capture, got {len(captures)}",
            condition=len(captures) == 1,
        )
    return 0


def require(message: str, *, condition: bool) -> None:
    """
    Raise AssertionError when a verification condition fails.

    Raises:
        AssertionError: If condition is false.

    """
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
