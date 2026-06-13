"""
`pytest_bdd.assets.docker.remote_xdist.verify_report` owns documented module behavior.

Responsibility:
    Post-execution verification of the NDJSON report produced by a remote xdist pytest run.
    Parses the NDJSON message stream, validates it against the cucumber-messages protocol
    schema, counts payload kinds (meta, test_run_started, test_run_finished, etc.), extracts
    worker IDs from TestCaseStarted messages, and applies verification-mode-specific assertions:
    "success" mode requires at least 2 distinct workers; "partial" mode requires exactly 1
    worker. Additionally supports console-write verification (--min-console-writes) and
    controller-only capture verification (--expect-controller-only) for live formatter tests.
    Raises SystemExit on success (return code 0) and AssertionError or ValueError on failure.

Reason for existence:
    The NDJSON report produced by pytest-bdd's message reporter contains structured data
    (cucumber-messages protocol) that must be validated to confirm that remote xdist message
    aggregation worked correctly — messages from multiple workers must be merged, worker IDs
    must be present, and the message stream must be schema-valid. This module encapsulates
    all post-run verification logic into a standalone script (invoked by controller_entrypoint
    via subprocess) so that verification failures are reported as distinct subprocess failures
    rather than being mixed into the pytest output. It imports from both the core pytest_bdd
    library (message_validation) and the testing utilities (message_stream_assertions) to
    leverage existing parsing and validation infrastructure.

Delegates:
    - _build_parser: Constructs the argparse ArgumentParser with report_path,
      verification_mode, transport_mode, --min-console-writes, and --expect-controller-only.
    - _load_fake_node_captures: Loads fake-node capture JSON files from the
      PYTEST_BDD_FAKE_NODE_CAPTURE_DIR for console-write verification.
    - parse_ndjson_messages (from pytest_bdd_testing.tool.message.stream_assertions):
      Parses the NDJSON file into a list of cucumber-messages dicts.
    - validate_message_stream (from pytest_bdd.model.message_validation): Validates the
      message stream against the cucumber-messages protocol schema.
    - count_payload_kinds (from message_stream_assertions): Counts occurrences of each
      message type.
    - worker_ids_for_payloads (from message_stream_assertions): Extracts worker_id values
      from messages of a given type.
    - require: A local assertion helper that raises AssertionError with a message when a
      condition is False.
    - cucumber_messages.TestCaseStarted: Imported as the type filter for worker_id extraction.

Cohesion:
    Every function in this module serves the report verification pipeline: parse CLI args →
    parse NDJSON → validate schema → count payloads → extract worker IDs → assert based on
    mode → verify console captures. The module is a cohesive verification script, not a
    library of reusable utilities.

Separation:
    - controller_entrypoint.py: Invokes verify_report as a subprocess after pytest completes;
      the controller does not contain verification logic itself. This separation allows
      verification to be tested independently of the controller orchestration.
    - message_stream_assertions (testing utility): Provides generic NDJSON parsing and
      counting functions; verify_report applies mode-specific assertions on top of them.
    - message_validation (core library): Provides protocol-level validation; verify_report
      uses it as a building block for acceptance-test-specific checks.

Main consumers:
    - controller_entrypoint.main: Runs verify_report as a subprocess via
      `python -m pytest_bdd_testing.assets.docker.remote_xdist.verify_report` after pytest.
    - Direct CLI invocation: Can be run standalone for debugging:
      `python verify_report.py <report.ndjson> <mode> <transport>`.

State and side effects:
    Reads the NDJSON report file from disk (via parse_ndjson_messages). Reads fake-node
    capture JSON files from PYTEST_BDD_FAKE_NODE_CAPTURE_DIR (via _load_fake_node_captures).
    No writes to filesystem. No environment variable writes. No pytest stash access.
    No subprocess calls.

Invariants:
    - MIN_SUCCESS_WORKERS is 2 — "success" mode always requires at least 2 distinct worker IDs.
    - "partial" mode requires exactly 1 worker ID (simulating partial transport failure).
    - Unknown verification_mode values raise ValueError (guarded by the else branch).
    - require() never returns when condition is False — it raises AssertionError.
    - main() returns 0 on success and raises SystemExit(main()) when run as __main__.

Failure semantics:
    require() raises AssertionError with a descriptive message when a condition fails.
    main() raises ValueError for unknown verification_mode values (via the else branch).
    main() returns 0 on success; when run as __main__, this is wrapped in SystemExit(main()).
    validate_message_stream may raise validation errors if the NDJSON is malformed (these
    propagate uncaught to the caller).

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=5
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=5
    #arch-eval:separation=5
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=5
    #arch-eval:entity_fullness=5
    #arch-eval:locational_stability=5
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from cucumber_messages import (
    TestCaseStarted as CucumberTestCaseStarted,  # type:ignore[attr-defined] — upstream type stubs missing this attribute
)

from pytest_bdd.model.message_validation import validate_message_stream
from pytest_bdd_testing.tool.message.stream_assertions import (
    count_payload_kinds,
    parse_ndjson_messages,
    worker_ids_for_payloads,
)

MIN_SUCCESS_WORKERS = 2


def _build_parser() -> argparse.ArgumentParser:
    """
    `verify_report._build_parser` owns documented function behavior.

    Responsibility:
        Constructs and returns an argparse.ArgumentParser with five arguments: report_path
        (positional, required — path to the NDJSON report file), verification_mode (optional,
        default "success"), transport_mode (optional, default "socket"), --min-console-writes
        (optional int, default 0 — minimum expected console write count from fake node
        captures), and --expect-controller-only (optional flag — asserts exactly one
        controller-owned formatter capture). No parsing is performed; the parser is returned
        for main() to use.

    Reason for existence:
        Centralizing argument definitions in a dedicated builder function keeps the CLI
        contract visible in one place and allows the argument definitions to be tested
        independently of the verification logic. The default values ("success", "socket", 0)
        reflect the most common test scenario (full success with socket transport, no
        console-write verification) so that the common case requires minimal arguments.

    Delegates:
        - argparse.ArgumentParser: The stdlib argument parser; configured with add_argument
          calls and returned for later .parse_args() invocation.

    Cohesion:
        The function does exactly one thing: build an ArgumentParser. All five argument
        definitions are aspects of the verify_report CLI interface. No parsing, no I/O.

    Separation:
        - verify_report.main: Calls _build_parser().parse_args() to obtain the options
          namespace. Separation keeps parser construction out of the verification logic.

    Main consumers:
        - verify_report.main: calls _build_parser().parse_args() to parse CLI arguments.

    State and side effects:
        None — pure ArgumentParser construction. No filesystem, environment, subprocess,
        or pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=5
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("report_path")
    parser.add_argument("verification_mode", nargs="?", default="success")
    parser.add_argument("transport_mode", nargs="?", default="socket")
    parser.add_argument("--min-console-writes", type=int, default=0)
    parser.add_argument("--expect-controller-only", action="store_true")
    return parser


def _load_fake_node_captures() -> list[dict[str, object]]:
    """
    `verify_report._load_fake_node_captures` owns documented function behavior.

    Responsibility:
        Loads fake-node capture data from JSON files in the directory specified by the
        PYTEST_BDD_FAKE_NODE_CAPTURE_DIR environment variable. Returns an empty list if the
        variable is unset or the directory does not exist. Otherwise, reads all *.json files
        in sorted order, parses each as JSON, and returns a list of deserialized dicts.
        These captures represent console-write counts and other metadata collected by the
        fake-node runtime during live formatter tests.

    Reason for existence:
        In "success-live" verification mode, the controller enables a fake Node.js runtime
        that intercepts @cucumber/cucumber formatter calls and writes capture data to JSON
        files. This function provides the bridge between those on-disk captures and the
        verification assertions (--min-console-writes, --expect-controller-only). It is
        extracted from main() to keep the capture-loading logic (env var reading, path
        existence checking, file globbing, JSON parsing) separate from the assertion logic.

    Delegates:
        - os.environ: Reads PYTEST_BDD_FAKE_NODE_CAPTURE_DIR.
        - pathlib.Path: Used for directory existence checking and file globbing (glob).
        - json.loads: Parses each capture JSON file into a Python dict.

    Cohesion:
        The function does exactly one thing: load capture files from a directory. All logic
        (env var check, path existence, glob, JSON parse) serves that single purpose.

    Separation:
        - verify_report.main: Consumes the returned capture list for console-write and
          controller-only assertions. Separation keeps I/O separate from business logic.

    Main consumers:
        - verify_report.main: calls _load_fake_node_captures() and uses the result for
          --min-console-writes and --expect-controller-only assertions.

    State and side effects:
        Reads the filesystem (Path.exists, Path.glob, Path.read_text). Reads
        PYTEST_BDD_FAKE_NODE_CAPTURE_DIR from os.environ. No writes, no subprocess,
        no pytest stash access.

    Architecture score:
        #arch-eval:reason_for_existence=3
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=5
    """
    capture_dir = os.environ.get("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", "").strip()
    if not capture_dir:
        return []
    path = Path(capture_dir)
    if not path.exists():
        return []
    return [json.loads(capture_path.read_text(encoding="utf-8")) for capture_path in sorted(path.glob("*.json"))]


def main() -> int:
    """
    `pytest_bdd.assets.docker.remote_xdist.verify_report.main` owns documented function behavior.

    Responsibility:
        The main verification orchestrator. Parses CLI arguments, resolves the report path,
        loads and validates the NDJSON message stream, counts payload kinds, extracts worker
        IDs, and applies a sequence of `require` assertions: message validation must pass,
        exactly one meta/test_run_started/test_run_finished message each, transport_mode must
        be one of socket/via/ssh, and worker count must match the verification mode (≥2 for
        "success", exactly 1 for "partial"). Then, if --min-console-writes is set, loads fake
        node captures and verifies the console write count meets the threshold. If
        --expect-controller-only is set, verifies exactly one capture exists. Returns 0 on
        success. Raises ValueError for unknown verification modes.

    Reason for existence:
        This function ties together all verification steps into a single sequential check:
        schema validation → payload counting → worker ID verification → capture verification.
        The `require` pattern (condition → AssertionError) makes each check self-documenting
        and produces clear failure messages. The function returns an int (0) for compatibility
        with sys.exit/SystemExit when invoked as __main__. It is separate from the controller
        entrypoint so that verification can be invoked and tested independently.

    Delegates:
        - _build_parser().parse_args(): Parses CLI arguments.
        - parse_ndjson_messages: Parses the NDJSON file into message dicts.
        - validate_message_stream: Validates the message stream against cucumber-messages schema.
        - count_payload_kinds: Counts occurrences of each message type.
        - worker_ids_for_payloads: Extracts worker_id values from TestCaseStarted messages.
        - _load_fake_node_captures: Loads fake-node capture JSON files.
        - require: Asserts conditions with descriptive messages.

    Cohesion:
        The function orchestrates a clear pipeline: parse → load → validate → count → assert
        workers → assert captures. Every step is a necessary part of the verification sequence.
        No unrelated logic.

    Separation:
        - controller_entrypoint.main: Invokes verify_report as a subprocess; the controller
          does not perform verification itself.
        - require: The assertion helper extracted to avoid repeating `if not condition: raise`
          patterns across main().

    Main consumers:
        - controller_entrypoint._build_verify_cmd: Builds the command that invokes this
          function via `python -m verify_report`.
        - Direct invocation: `python verify_report.py <report> <mode> <transport>`.

    State and side effects:
        Reads the NDJSON report file from disk. Reads fake-node capture JSON files from disk
        (when --min-console-writes or --expect-controller-only is used). No writes, no
        environment variable writes, no subprocess calls, no pytest stash access.

    Failure semantics:
        Raises ValueError(f"Unknown verification mode: {verification_mode}") for modes other
        than "success" or "partial". Raises AssertionError via require() for any failed
        assertion (message validation failure, wrong payload counts, wrong worker count,
        insufficient console writes, wrong capture count). These propagate to the caller
        (controller_entrypoint) which runs this with check=True, causing the controller
        subprocess to fail.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=5
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=5
        #arch-eval:locational_stability=5
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
    `pytest_bdd.assets.docker.remote_xdist.verify_report.require` owns documented function behavior.

    Responsibility:
        A minimal assertion helper that raises AssertionError with a descriptive message when
        a keyword-only `condition` is False. The message is the first positional argument.
        This function exists to make verification assertions in main() more readable by
        avoiding repeated `if not X: raise AssertionError(...)` patterns and by making the
        assertion intent explicit at the call site. The keyword-only `condition` parameter
        forces callers to name the condition, improving readability.

    Reason for existence:
        The main() function performs ~10 sequential assertions on the parsed message stream.
        Inlining `if not condition: raise AssertionError(msg)` at each call site would be
        verbose and obscure the assertion flow. Extracting this as a named `require` function
        makes each check read as a declarative statement (e.g., `require("message validation
        must pass", condition=validation_result.status == "pass")`). The keyword-only
        `condition` parameter prevents accidental swapping of message and condition.

    Delegates:
        - None — the function is a pure conditional + raise with no sub-delegation.

    Cohesion:
        The function does exactly one thing: check a condition and raise on failure. Its
        entire body is `if not condition: raise AssertionError(message)`. No unrelated logic.

    Separation:
        - verify_report.main: The sole consumer; require is extracted to avoid assertion
          boilerplate in the orchestrator function.
        - pytest standard assertions: require() complements but does not replace pytest
          assertions — it is used in a standalone script context where pytest is not running.

    Main consumers:
        - verify_report.main: calls require() for every verification assertion (message
          validation status, payload counts, worker IDs, console writes, capture counts).

    State and side effects:
        None — pure function. No filesystem, environment, subprocess, or pytest stash access.
        The only side effect is raising AssertionError when the condition is False.

    Failure semantics:
        Raises AssertionError(message) when condition is False. The message is provided by
        the caller and should describe what was expected. The AssertionError propagates to
        main()'s caller, which in practice is controller_entrypoint running verify_report
        with subprocess.run(check=True) — causing the subprocess to fail with exit code 1.

    Architecture score:
        #arch-eval:reason_for_existence=2
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=1
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=5
        #arch-eval:state_invariants=5
        #arch-eval:entity_fullness=1
        #arch-eval:locational_stability=5
    """
    if not condition:
        raise AssertionError(message)


if __name__ == "__main__":
    raise SystemExit(main())
