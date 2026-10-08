"""Convert a complete Cucumber Messages stream to standalone Allure files."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import tempfile
from base64 import b64decode
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import ValidationError

from pytest_cuke.model.message_converter import envelope_from_dict
from pytest_cuke.model.message_extension import PAYLOAD_KINDS, get_payload_kind
from pytest_cuke.model.message_validation import validate_envelope_data

if TYPE_CHECKING:
    from pytest_cuke.model import message_types as messages


class AllureConversionError(Exception):
    """An input stream cannot be converted to Allure results."""


@dataclass(frozen=True)
class _ParsedMessages:
    envelopes: list[messages.Envelope]
    exception_traces: dict[tuple[str, str], str]
    run_finished_trace: str | None
    raw_extensions: list[bytes]
    run_hook_traces: dict[str, str]


@dataclass(frozen=True)
class _NormalizedEnvelope:
    validation_payload: dict[str, Any]
    step_trace: str | None
    run_trace: str | None
    run_hook_trace: tuple[str, str] | None


def convert_allure_messages(input_path: Path, output_dir: Path) -> None:
    """Convert every completed scenario attempt in one Cucumber Messages run."""
    parsed = _read_envelopes(input_path)
    converted, attachments, results_by_case_id = _convert_scenarios(parsed.envelopes, parsed.exception_traces)
    run_hook_container, run_hook_attachments = _convert_run_hooks(
        parsed.envelopes, converted, parsed.run_hook_traces
    )
    attachments.extend(run_hook_attachments)
    _materialize_unscoped_attachments(parsed.envelopes, converted, attachments, results_by_case_id)
    _attach_run_diagnostics(
        converted,
        attachments,
        _one(parsed.envelopes, "test_run_finished"),
        parsed.run_finished_trace,
    )
    _attach_raw_extensions(converted, attachments, parsed.raw_extensions)
    artifacts = _render_artifacts(converted, attachments, run_hook_container)

    try:
        _write_artifacts_transactionally(output_dir, artifacts)
    except AllureConversionError:
        raise
    except OSError as exc:
        raise AllureConversionError(f"cannot write Allure results to {output_dir}: {exc}") from exc


def _read_envelopes(
    input_path: Path,
) -> _ParsedMessages:
    try:
        raw_content = input_path.read_bytes()
    except OSError as exc:
        raise AllureConversionError(f"cannot read input {input_path}: {exc}") from exc
    try:
        raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AllureConversionError(f"input is not valid UTF-8: {input_path}") from exc

    envelopes: list[messages.Envelope] = []
    exception_traces: dict[tuple[str, str], str] = {}
    run_finished_trace: str | None = None
    raw_extensions: list[bytes] = []
    run_hook_traces: dict[str, str] = {}
    known_payload_names = _known_payload_names()
    raw_lines = raw_content.split(b"\n")
    for line_number, raw_line in enumerate(raw_lines, start=1):
        line_bytes = raw_line[:-1] if raw_line.endswith(b"\r") and line_number < len(raw_lines) else raw_line
        line = line_bytes.decode("utf-8")
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AllureConversionError(f"invalid JSON in {input_path} at line {line_number}: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise AllureConversionError(f"Cucumber message in {input_path} at line {line_number} must be an object")
        unknown_fields = set(payload) - known_payload_names
        if unknown_fields:
            if len(payload) == 1 and len(unknown_fields) == 1:
                raw_extensions.append(line_bytes)
                continue
            names = ", ".join(sorted(repr(name) for name in unknown_fields))
            raise AllureConversionError(
                f"invalid Cucumber message in {input_path} at line {line_number}: "
                f"unknown top-level payload field(s) {names}"
            )
        diagnostics = validate_envelope_data(payload, position=line_number)
        if diagnostics:
            details = "; ".join(
                f"{'.'.join(str(part) for part in diagnostic.instance_path)}: {diagnostic.message}"
                if diagnostic.instance_path
                else diagnostic.message
                for diagnostic in diagnostics
            )
            raise AllureConversionError(
                f"invalid Cucumber message in {input_path} at line {line_number}: {details}"
            )
        normalized = _without_exception_stack_trace(payload)
        try:
            envelope = envelope_from_dict(normalized.validation_payload)
        except (TypeError, ValueError, ValidationError) as exc:
            detail = _validation_summary(exc)
            raise AllureConversionError(
                f"invalid Cucumber message in {input_path} at line {line_number}: {detail}"
            ) from exc
        envelopes.append(envelope)
        if normalized.step_trace is not None:
            if envelope.test_step_finished is None:
                raise AllureConversionError(
                    f"exception stack trace in {input_path} at line {line_number} has no test step"
                )
            key = (envelope.test_step_finished.test_case_started_id, envelope.test_step_finished.test_step_id)
            if key in exception_traces:
                raise AllureConversionError(f"duplicate exception stack trace in {input_path} at line {line_number}")
            exception_traces[key] = normalized.step_trace
        if normalized.run_trace is not None:
            if envelope.test_run_finished is None:
                raise AllureConversionError(
                    f"run exception stack trace in {input_path} at line {line_number} has no test run finish"
                )
            if run_finished_trace is not None:
                raise AllureConversionError(
                    f"duplicate run exception stack trace in {input_path} at line {line_number}"
                )
            run_finished_trace = normalized.run_trace
        if normalized.run_hook_trace is not None:
            started_id, trace = normalized.run_hook_trace
            if started_id in run_hook_traces:
                raise AllureConversionError(
                    f"duplicate run hook exception stack trace in {input_path} at line {line_number}"
                )
            run_hook_traces[started_id] = trace

    if not envelopes:
        raise AllureConversionError(f"input contains no Cucumber messages: {input_path}")
    return _ParsedMessages(envelopes, exception_traces, run_finished_trace, raw_extensions, run_hook_traces)


def _known_payload_names() -> set[str]:
    names = set(PAYLOAD_KINDS)
    names.update(_camel_payload_name(kind) for kind in PAYLOAD_KINDS)
    return names


def _camel_payload_name(kind: str) -> str:
    first, *rest = kind.split("_")
    return first + "".join(part.title() for part in rest)


def _without_exception_stack_trace(
    payload: dict[str, Any],
) -> _NormalizedEnvelope:
    """Keep schema-valid stackTrace data despite the older generated messages model."""
    step_trace: str | None = None
    run_trace: str | None = None
    run_hook_trace: tuple[str, str] | None = None
    validation_payload = payload

    for event_key in ("testStepFinished", "test_step_finished"):
        test_step_finished = payload.get(event_key)
        if not isinstance(test_step_finished, dict):
            continue
        for result_key in ("testStepResult", "test_step_result"):
            test_step_result = test_step_finished.get(result_key)
            if not isinstance(test_step_result, dict):
                continue
            exception = test_step_result.get("exception")
            if isinstance(exception, dict) and "stackTrace" in exception:
                step_trace = _stack_trace_value(exception)
                validation_payload = _payload_without_stack_trace(
                    payload,
                    event_key,
                    exception,
                    nested_result_key=result_key,
                )
                break
        break

    for event_key in ("testRunFinished", "test_run_finished"):
        test_run_finished = payload.get(event_key)
        if not isinstance(test_run_finished, dict):
            continue
        exception = test_run_finished.get("exception")
        if isinstance(exception, dict) and "stackTrace" in exception:
            run_trace = _stack_trace_value(exception)
            validation_payload = _payload_without_stack_trace(payload, event_key, exception)
        break

    for event_key in ("testRunHookFinished", "test_run_hook_finished"):
        test_run_hook_finished = payload.get(event_key)
        if not isinstance(test_run_hook_finished, dict):
            continue
        test_run_hook_result = test_run_hook_finished.get("result")
        if isinstance(test_run_hook_result, dict):
            exception = test_run_hook_result.get("exception")
            if isinstance(exception, dict) and "stackTrace" in exception:
                started_id = test_run_hook_finished.get(
                    "testRunHookStartedId", test_run_hook_finished.get("test_run_hook_started_id")
                )
                if not isinstance(started_id, str) or not started_id:
                    raise AllureConversionError("test run hook exception stack trace has no started hook id")
                run_hook_trace = (started_id, _stack_trace_value(exception))
                validation_payload = _payload_without_stack_trace(
                    payload,
                    event_key,
                    exception,
                    nested_result_key="result",
                )
        break

    return _NormalizedEnvelope(validation_payload, step_trace, run_trace, run_hook_trace)


def _stack_trace_value(exception: dict[str, Any]) -> str:
    stack_trace = exception.get("stackTrace")
    if not isinstance(stack_trace, str):
        raise AllureConversionError("Cucumber exception stackTrace must be a string")
    return stack_trace


def _payload_without_stack_trace(
    payload: dict[str, Any], event_key: str, exception: dict[str, Any], nested_result_key: str | None = None
) -> dict[str, Any]:
    validation_payload = dict(payload)
    event = payload[event_key]
    if not isinstance(event, dict):
        raise AllureConversionError(f"Cucumber message payload {event_key!r} must be an object")
    validation_event = dict(event)
    validation_exception = dict(exception)
    del validation_exception["stackTrace"]
    if nested_result_key is None:
        validation_event["exception"] = validation_exception
    else:
        nested_result = validation_event.get(nested_result_key)
        if not isinstance(nested_result, dict):
            raise AllureConversionError(f"Cucumber result {nested_result_key!r} must be an object")
        validation_result = dict(nested_result)
        validation_result["exception"] = validation_exception
        validation_event[nested_result_key] = validation_result
    validation_payload[event_key] = validation_event
    return validation_payload


def _validation_summary(error: Exception) -> str:
    if isinstance(error, ValidationError):
        details = error.errors()
        return "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}" for item in details
        )
    return str(error)


def _convert_scenarios(
    envelopes: list[messages.Envelope], exception_traces: dict[tuple[str, str], str]
) -> tuple[
    list[tuple[dict[str, Any], dict[str, Any]]],
    list[tuple[str, bytes]],
    dict[str, list[dict[str, Any]]],
]:
    pickles = _index_by_id(_messages(envelopes, "pickle"), "pickle")
    test_cases = _index_by_id(_messages(envelopes, "test_case"), "test case")
    hooks = _index_by_id(_messages(envelopes, "hook"), "hook")
    run_started = _one(envelopes, "test_run_started")
    run_finished = _one(envelopes, "test_run_finished")

    if not pickles:
        raise AllureConversionError("Cucumber run contains no pickle messages")
    if not test_cases:
        raise AllureConversionError("Cucumber run contains no test case messages")

    cases_by_pickle: dict[str, Any] = {}
    for test_case in test_cases.values():
        if test_case.pickle_id not in pickles:
            raise AllureConversionError(
                f"test case {test_case.id!r} refers to missing pickle {test_case.pickle_id!r}"
            )
        if test_case.pickle_id in cases_by_pickle:
            raise AllureConversionError(f"multiple test cases refer to pickle {test_case.pickle_id!r}")
        cases_by_pickle[test_case.pickle_id] = test_case
        _validate_test_case_steps(test_case, pickles[test_case.pickle_id], hooks)
    for pickle_id in pickles:
        if pickle_id not in cases_by_pickle:
            raise AllureConversionError(f"pickle {pickle_id!r} has no test case")

    attempts = _validate_run_lifecycle(envelopes, run_started, run_finished, test_cases)
    _validate_exception_traces(exception_traces, attempts, test_cases)
    converted: list[tuple[dict[str, Any], dict[str, Any]]] = []
    attachment_files: list[tuple[str, bytes]] = []
    results_by_case_id: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts.values():
        test_case = test_cases[attempt["started"].test_case_id]
        pickle = pickles[test_case.pickle_id]
        result, container, files = _convert_attempt(
            envelopes,
            exception_traces,
            test_case,
            pickle,
            attempt,
            hooks,
        )
        converted.append((result, container))
        results_by_case_id.setdefault(test_case.id, []).append(result)
        attachment_files.extend(files)
    return converted, attachment_files, results_by_case_id


def _messages(envelopes: list[messages.Envelope], kind: str) -> list[Any]:
    return [getattr(envelope, kind) for envelope in envelopes if get_payload_kind(envelope) == kind]


def _one(envelopes: list[messages.Envelope], kind: str) -> Any:
    matches = _messages(envelopes, kind)
    if len(matches) != 1:
        raise AllureConversionError(
            f"expected exactly one {kind.replace('_', ' ')} message, found {len(matches)}"
        )
    return matches[0]


def _index_by_id(items: list[Any], kind: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in items:
        if item.id in result:
            raise AllureConversionError(f"duplicate {kind} id {item.id!r}")
        result[item.id] = item
    return result


def _validate_test_case_steps(test_case: Any, pickle: Any, hooks: dict[str, Any]) -> None:
    pickle_steps = _index_by_id(pickle.steps, f"pickle step in pickle {pickle.id!r}")
    test_step_ids: set[str] = set()
    represented_pickle_steps: set[str] = set()
    for test_step in test_case.test_steps:
        if test_step.id in test_step_ids:
            raise AllureConversionError(f"test case {test_case.id!r} has duplicate test step id {test_step.id!r}")
        test_step_ids.add(test_step.id)
        has_pickle_step = test_step.pickle_step_id is not None
        has_hook = test_step.hook_id is not None
        if has_pickle_step == has_hook:
            raise AllureConversionError(
                f"test step {test_step.id!r} in test case {test_case.id!r} must reference exactly one pickle step or hook"
            )
        if has_pickle_step:
            if test_step.pickle_step_id not in pickle_steps:
                raise AllureConversionError(
                    f"test step {test_step.id!r} refers to missing pickle step {test_step.pickle_step_id!r}"
                )
            if test_step.pickle_step_id in represented_pickle_steps:
                raise AllureConversionError(
                    f"test case {test_case.id!r} maps pickle step {test_step.pickle_step_id!r} more than once"
                )
            represented_pickle_steps.add(test_step.pickle_step_id)
        elif test_step.hook_id not in hooks:
            raise AllureConversionError(f"test step {test_step.id!r} refers to missing hook {test_step.hook_id!r}")
    if represented_pickle_steps != set(pickle_steps):
        missing = sorted(set(pickle_steps) - represented_pickle_steps)
        raise AllureConversionError(f"test case {test_case.id!r} does not represent pickle steps {missing!r}")


def _validate_run_lifecycle(
    envelopes: list[messages.Envelope],
    run_started: Any,
    run_finished: Any,
    test_cases: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    run_started_positions = [pos for pos, env in enumerate(envelopes) if env.test_run_started is not None]
    run_finished_positions = [pos for pos, env in enumerate(envelopes) if env.test_run_finished is not None]
    run_started_position = run_started_positions[0]
    run_finished_position = run_finished_positions[0]
    if run_started_position >= run_finished_position:
        raise AllureConversionError("test run finished before it started")

    attempts: dict[str, dict[str, Any]] = {}
    case_finishes: dict[str, tuple[int, Any]] = {}
    step_starts: dict[tuple[str, str], tuple[int, Any]] = {}
    step_finishes: dict[tuple[str, str], tuple[int, Any]] = {}
    for position, envelope in enumerate(envelopes):
        if envelope.test_case_started is not None:
            case_started = envelope.test_case_started
            if case_started.id in attempts:
                raise AllureConversionError(f"duplicate test attempt id {case_started.id!r}")
            if case_started.test_case_id not in test_cases:
                raise AllureConversionError(
                    f"test attempt {case_started.id!r} refers to missing test case {case_started.test_case_id!r}"
                )
            attempts[case_started.id] = {"started": case_started, "start_position": position}
        elif envelope.test_case_finished is not None:
            case_finished = envelope.test_case_finished
            attempt_id = case_finished.test_case_started_id
            if attempt_id in case_finishes:
                raise AllureConversionError(f"duplicate test case finish for attempt {attempt_id!r}")
            case_finishes[attempt_id] = (position, case_finished)
        elif envelope.test_step_started is not None:
            step_started = envelope.test_step_started
            key = (step_started.test_case_started_id, step_started.test_step_id)
            if key in step_starts:
                raise AllureConversionError(
                    f"duplicate test step start for attempt {key[0]!r}, step {key[1]!r}"
                )
            step_starts[key] = (position, step_started)
        elif envelope.test_step_finished is not None:
            step_finished = envelope.test_step_finished
            key = (step_finished.test_case_started_id, step_finished.test_step_id)
            if key in step_finishes:
                raise AllureConversionError(
                    f"duplicate test step finish for attempt {key[0]!r}, step {key[1]!r}"
                )
            step_finishes[key] = (position, step_finished)

    if not attempts:
        raise AllureConversionError("Cucumber run contains no test attempts")
    if set(case_finishes) != set(attempts):
        missing_finishes = sorted(set(attempts) - set(case_finishes))
        unknown_finishes = sorted(set(case_finishes) - set(attempts))
        if missing_finishes:
            raise AllureConversionError(f"test attempts did not finish: {missing_finishes!r}")
        raise AllureConversionError(f"test case finishes refer to unknown attempts: {unknown_finishes!r}")
    _validate_retry_sequences(attempts, case_finishes)

    if set(step_starts) != set(step_finishes):
        missing_step_finishes = sorted(set(step_starts) - set(step_finishes), key=lambda key: (key[0], key[1]))
        missing_step_starts = sorted(set(step_finishes) - set(step_starts), key=lambda key: (key[0], key[1]))
        if missing_step_finishes:
            raise AllureConversionError(f"test steps did not finish: {missing_step_finishes!r}")
        raise AllureConversionError(f"test step finishes have no matching start: {missing_step_starts!r}")

    attempted_cases = {attempt["started"].test_case_id for attempt in attempts.values()}
    if attempted_cases != set(test_cases):
        unstarted = sorted(set(test_cases) - attempted_cases)
        raise AllureConversionError(f"test cases have no completed attempt: {unstarted!r}")

    run_start_time = _timestamp_nanos(run_started.timestamp)
    run_finish_time = _timestamp_nanos(run_finished.timestamp)
    if run_start_time > run_finish_time:
        raise AllureConversionError("test run timestamps are out of order")

    for attempt_id, attempt in attempts.items():
        started = attempt["started"]
        start_position = attempt["start_position"]
        finish_position, finished = case_finishes[attempt_id]
        if not run_started_position < start_position < finish_position < run_finished_position:
            raise AllureConversionError(f"test attempt {attempt_id!r} is outside the test run lifecycle")
        if _timestamp_nanos(run_started.timestamp) > _timestamp_nanos(started.timestamp):
            raise AllureConversionError(f"test attempt {attempt_id!r} starts before the run timestamp")
        if _timestamp_nanos(started.timestamp) > _timestamp_nanos(finished.timestamp):
            raise AllureConversionError(f"test attempt {attempt_id!r} timestamps are out of order")
        if _timestamp_nanos(finished.timestamp) > run_finish_time:
            raise AllureConversionError(f"test attempt {attempt_id!r} finishes after the run timestamp")
        attempt["finish_position"] = finish_position
        attempt["finished"] = finished
        attempt["step_positions"] = {}

        test_case = test_cases[started.test_case_id]
        previous_position = start_position
        previous_time = _timestamp_nanos(started.timestamp)
        expected_keys = {(attempt_id, test_step.id) for test_step in test_case.test_steps}
        observed_keys = {key for key in step_starts if key[0] == attempt_id}
        if observed_keys != expected_keys:
            missing = sorted(expected_keys - observed_keys)
            unknown = sorted(observed_keys - expected_keys)
            if missing:
                raise AllureConversionError(f"test attempt {attempt_id!r} is missing test step starts: {missing!r}")
            raise AllureConversionError(f"test attempt {attempt_id!r} has unknown test step starts: {unknown!r}")
        for test_step in test_case.test_steps:
            key = (attempt_id, test_step.id)
            start_pos, step_started = step_starts[key]
            finish_pos, step_finished = step_finishes[key]
            if not start_position < start_pos < finish_pos < finish_position:
                raise AllureConversionError(
                    f"test step {test_step.id!r} is outside attempt {attempt_id!r} lifecycle"
                )
            if start_pos <= previous_position:
                raise AllureConversionError(f"test attempt {attempt_id!r} test steps are not in declared order")
            started_at = _timestamp_nanos(step_started.timestamp)
            finished_at = _timestamp_nanos(step_finished.timestamp)
            if started_at < previous_time or finished_at < started_at:
                raise AllureConversionError(
                    f"test step {test_step.id!r} timestamps are out of order in attempt {attempt_id!r}"
                )
            previous_position = finish_pos
            previous_time = finished_at
            attempt["step_positions"][test_step.id] = (start_pos, finish_pos)
        if previous_position >= finish_position:
            raise AllureConversionError(f"test attempt {attempt_id!r} finishes before its last test step")
        if previous_time > _timestamp_nanos(finished.timestamp):
            raise AllureConversionError(f"test attempt {attempt_id!r} finishes before its last step timestamp")

    known_attempt_ids = set(attempts)
    for attempt_id, _step_id in (*step_starts.keys(), *step_finishes.keys()):
        if attempt_id not in known_attempt_ids:
            raise AllureConversionError(f"test step event refers to unknown attempt {attempt_id!r}")
    for envelope in envelopes:
        if (
            envelope.attachment is not None
            and envelope.attachment.test_case_started_id is not None
            and envelope.attachment.test_case_started_id not in known_attempt_ids
        ):
            raise AllureConversionError(
                f"attachment {envelope.attachment.file_name or '<unnamed>'!r} refers to unknown attempt "
                f"{envelope.attachment.test_case_started_id!r}"
            )
    return attempts


def _validate_retry_sequences(
    attempts: dict[str, dict[str, Any]],
    case_finishes: dict[str, tuple[int, Any]],
) -> None:
    attempts_by_case: dict[str, list[tuple[int, str, int, Any]]] = {}
    for attempt_id, attempt in attempts.items():
        started = attempt["started"]
        attempt_number = started.attempt
        if not isinstance(attempt_number, int) or isinstance(attempt_number, bool) or attempt_number < 0:
            raise AllureConversionError(
                f"test attempt {attempt_id!r} has invalid attempt number {attempt_number!r}"
            )
        finish_position, finished = case_finishes[attempt_id]
        attempts_by_case.setdefault(started.test_case_id, []).append(
            (attempt_number, attempt_id, attempt["start_position"], (finish_position, finished))
        )

    for test_case_id, case_attempts in attempts_by_case.items():
        case_attempts.sort(key=lambda item: item[0])
        observed_numbers: set[int] = set()
        for expected_number, (attempt_number, attempt_id, start_position, finish_data) in enumerate(case_attempts):
            if attempt_number in observed_numbers:
                raise AllureConversionError(
                    f"test case {test_case_id!r} has duplicate retry attempt number {attempt_number}"
                )
            observed_numbers.add(attempt_number)
            if attempt_number != expected_number:
                raise AllureConversionError(
                    f"test case {test_case_id!r} retry attempts must be contiguous from 0; "
                    f"expected {expected_number}, found {attempt_number}"
                )

            finish_position, finished = finish_data
            has_next = expected_number + 1 < len(case_attempts)
            if has_next:
                if not finished.will_be_retried:
                    raise AllureConversionError(
                        f"non-final attempt {attempt_id!r} for test case {test_case_id!r} "
                        "has willBeRetried=false"
                    )
                next_attempt_number, next_attempt_id, next_start_position, _ = case_attempts[expected_number + 1]
                if next_start_position <= finish_position:
                    raise AllureConversionError(
                        f"retry attempt {next_attempt_number} for test case {test_case_id!r} "
                        f"started before attempt {attempt_number} finished"
                    )
                previous_finish_time = _timestamp_nanos(finished.timestamp)
                next_start_time = _timestamp_nanos(attempts[next_attempt_id]["started"].timestamp)
                if next_start_time < previous_finish_time:
                    raise AllureConversionError(
                        f"retry attempt {next_attempt_number} for test case {test_case_id!r} "
                        f"has a timestamp before attempt {attempt_number} finished"
                    )
            elif finished.will_be_retried:
                raise AllureConversionError(
                    f"test case {test_case_id!r} attempt {attempt_number} declares a retry, "
                    f"but attempt {attempt_number + 1} is missing at end of stream"
                )


def _validate_exception_traces(
    exception_traces: dict[tuple[str, str], str],
    attempts: dict[str, dict[str, Any]],
    test_cases: dict[str, Any],
) -> None:
    for attempt_id, step_id in exception_traces:
        attempt = attempts.get(attempt_id)
        if attempt is None:
            raise AllureConversionError(f"exception stack trace refers to unknown attempt {attempt_id!r}")
        test_case = test_cases[attempt["started"].test_case_id]
        if step_id not in {test_step.id for test_step in test_case.test_steps}:
            raise AllureConversionError(
                f"exception stack trace refers to unknown test step {step_id!r} in attempt {attempt_id!r}"
            )


def _convert_run_hooks(
    envelopes: list[messages.Envelope],
    converted: list[tuple[dict[str, Any], dict[str, Any]]],
    run_hook_traces: dict[str, str],
) -> tuple[dict[str, Any] | None, list[tuple[str, bytes]]]:
    """Map Cucumber test-run hooks to a shared Allure fixture container."""
    run_started = _one(envelopes, "test_run_started")
    run_finished = _one(envelopes, "test_run_finished")
    hooks = _index_by_id(_messages(envelopes, "hook"), "hook")
    run_started_position = next(pos for pos, env in enumerate(envelopes) if env.test_run_started is not None)
    run_finished_position = next(pos for pos, env in enumerate(envelopes) if env.test_run_finished is not None)
    case_started_positions = [pos for pos, env in enumerate(envelopes) if env.test_case_started is not None]
    case_finished_positions = [pos for pos, env in enumerate(envelopes) if env.test_case_finished is not None]
    run_start_time = _timestamp_nanos(run_started.timestamp)
    run_finish_time = _timestamp_nanos(run_finished.timestamp)
    if run_finished.test_run_started_id is not None and run_finished.test_run_started_id != run_started.id:
        raise AllureConversionError("test run finished refers to a different test run start")

    starts: dict[str, tuple[int, Any, Any, str]] = {}
    finishes: dict[str, tuple[int, Any]] = {}
    active_started_id: str | None = None
    for position, envelope in enumerate(envelopes):
        started = envelope.test_run_hook_started
        if started is not None:
            if active_started_id is not None:
                raise AllureConversionError("test run hooks overlap in the Messages stream")
            if started.id in starts:
                raise AllureConversionError(f"duplicate test run hook start {started.id!r}")
            if not run_started_position < position < run_finished_position:
                raise AllureConversionError(f"test run hook {started.id!r} is outside the test run lifecycle")
            if run_started.id is None or started.test_run_started_id != run_started.id:
                raise AllureConversionError(
                    f"test run hook {started.id!r} refers to an unknown test run {started.test_run_started_id!r}"
                )
            hook = hooks.get(started.hook_id)
            if hook is None:
                raise AllureConversionError(
                    f"test run hook {started.id!r} refers to unknown hook {started.hook_id!r}"
                )
            hook_type = getattr(hook.type, "value", hook.type)
            if hook_type not in {"BEFORE_TEST_RUN", "AFTER_TEST_RUN"}:
                raise AllureConversionError(
                    f"hook {hook.id!r} has unsupported test run hook type {hook_type!r}"
                )
            before_case_started = hook_type == "BEFORE_TEST_RUN" and any(
                case_position < position for case_position in case_started_positions
            )
            if before_case_started:
                raise AllureConversionError(f"before-test-run hook {hook.id!r} started after a test case")
            if hook_type == "AFTER_TEST_RUN" and any(
                case_position > position for case_position in case_finished_positions
            ):
                raise AllureConversionError(f"after-test-run hook {hook.id!r} started before all test cases finished")
            hook_start_time = _timestamp_nanos(started.timestamp)
            if not run_start_time <= hook_start_time <= run_finish_time:
                raise AllureConversionError(f"test run hook {started.id!r} timestamp is outside the test run")
            starts[started.id] = (position, started, hook, hook_type)
            active_started_id = started.id
            continue

        finished = envelope.test_run_hook_finished
        if finished is None:
            continue
        started_id = finished.test_run_hook_started_id
        if started_id in finishes:
            raise AllureConversionError(f"duplicate test run hook finish for {started_id!r}")
        started_entry = starts.get(started_id)
        if started_entry is None:
            raise AllureConversionError(f"test run hook finish refers to unknown start {started_id!r}")
        if active_started_id != started_id:
            raise AllureConversionError(f"test run hook {started_id!r} finished out of order")
        start_position, started, _hook, _hook_type = started_entry
        if not start_position < position < run_finished_position:
            raise AllureConversionError(f"test run hook {started_id!r} finish is outside its lifecycle")
        hook_finish_time = _timestamp_nanos(finished.timestamp)
        if not _timestamp_nanos(started.timestamp) <= hook_finish_time <= run_finish_time:
            raise AllureConversionError(f"test run hook {started_id!r} timestamps are out of order")
        finishes[started_id] = (position, finished)
        active_started_id = None

    if active_started_id is not None:
        raise AllureConversionError(f"test run hook {active_started_id!r} did not finish")
    missing_finishes = sorted(set(starts) - set(finishes))
    if missing_finishes:
        raise AllureConversionError(f"test run hooks did not finish: {missing_finishes!r}")
    unknown_traces = sorted(set(run_hook_traces) - set(starts))
    if unknown_traces:
        raise AllureConversionError(f"test run hook exception traces refer to unknown hooks: {unknown_traces!r}")

    before_fixtures: list[tuple[int, dict[str, Any]]] = []
    after_fixtures: list[tuple[int, dict[str, Any]]] = []
    fixtures_by_started_id: dict[str, dict[str, Any]] = {}
    for started_id, (start_position, started, hook, hook_type) in sorted(
        starts.items(), key=lambda item: item[1][0]
    ):
        finished = finishes[started_id][1]
        result = finished.result
        status = _allure_status(result.status.value)
        details = _status_details(result, run_hook_traces.get(started_id))
        default_name = "Before test run" if hook_type == "BEFORE_TEST_RUN" else "After test run"
        fixture: dict[str, Any] = {
            "uuid": str(uuid4()),
            "name": hook.name or default_name,
            "status": status,
            "stage": "finished",
            "start": _timestamp_millis(started.timestamp),
            "stop": _timestamp_millis(finished.timestamp),
        }
        if details:
            fixture["statusDetails"] = details
        fixtures_by_started_id[started_id] = fixture
        fixture_group = before_fixtures if hook_type == "BEFORE_TEST_RUN" else after_fixtures
        fixture_group.append((start_position, fixture))

    attachment_files: list[tuple[str, bytes]] = []
    for position, envelope in enumerate(envelopes):
        attachment = envelope.attachment
        if attachment is None or attachment.test_run_hook_started_id is None:
            continue
        started_id = attachment.test_run_hook_started_id
        fixture_target = fixtures_by_started_id.get(started_id)
        lifecycle = starts.get(started_id)
        finish = finishes.get(started_id)
        if fixture_target is None or lifecycle is None or finish is None:
            raise AllureConversionError(
                f"attachment {attachment.file_name or '<unnamed>'!r} refers to unknown test run hook {started_id!r}"
            )
        if attachment.test_case_started_id is not None or attachment.test_step_id is not None:
            raise AllureConversionError(
                f"attachment {attachment.file_name or '<unnamed>'!r} has conflicting test run and case correlations"
            )
        if (
            attachment.test_run_started_id is not None
            and attachment.test_run_started_id != run_started.id
        ):
            raise AllureConversionError(
                f"attachment {attachment.file_name or '<unnamed>'!r} refers to an unknown test run "
                f"{attachment.test_run_started_id!r}"
            )
        if not lifecycle[0] < position < finish[0]:
            raise AllureConversionError(
                f"attachment {attachment.file_name or '<unnamed>'!r} is outside test run hook {started_id!r}"
            )
        _materialize_attachment(attachment, fixture_target, attachment_files)

    if not before_fixtures and not after_fixtures:
        return None, attachment_files
    run_hook_container = {
        "uuid": str(uuid4()),
        "children": [result["uuid"] for result, _container in converted],
        "befores": [fixture for _position, fixture in before_fixtures],
        "afters": [fixture for _position, fixture in after_fixtures],
    }
    return run_hook_container, attachment_files


def _convert_attempt(
    envelopes: list[messages.Envelope],
    exception_traces: dict[tuple[str, str], str],
    test_case: Any,
    pickle: Any,
    attempt: dict[str, Any],
    hooks: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[tuple[str, bytes]]]:
    attempt_id = attempt["started"].id
    case_started = attempt["started"]
    case_finished = attempt["finished"]
    case_started_position = attempt["start_position"]
    case_finished_position = attempt["finish_position"]
    step_event_positions = attempt["step_positions"]
    pickle_steps = {step.id: step for step in pickle.steps}
    scenario_steps: list[dict[str, Any]] = []
    before_fixtures: list[dict[str, Any]] = []
    after_fixtures: list[dict[str, Any]] = []
    step_targets: dict[str, dict[str, Any]] = {}
    status_details_candidates: list[tuple[str, dict[str, str]]] = []
    statuses: list[str] = []

    for test_step in test_case.test_steps:
        started = _step_message(envelopes, "test_step_started", attempt_id, test_step.id)
        finished = _step_message(envelopes, "test_step_finished", attempt_id, test_step.id)
        status = _allure_status(finished.test_step_result.status.value)
        statuses.append(status)
        details = _status_details(
            finished.test_step_result,
            exception_traces.get((attempt_id, test_step.id)),
        )
        if test_step.pickle_step_id is not None:
            pickle_step = pickle_steps[test_step.pickle_step_id]
            step_result: dict[str, Any] = {
                "name": pickle_step.text,
                "status": status,
                "stage": "finished",
                "start": _timestamp_millis(started.timestamp),
                "stop": _timestamp_millis(finished.timestamp),
            }
            argument_presentation = _pickle_step_argument_presentation(pickle_step)
            if argument_presentation is not None:
                step_result.update(argument_presentation)
            if details:
                step_result["statusDetails"] = details
                if status != "passed":
                    status_details_candidates.append((status, details))
            scenario_steps.append(step_result)
            step_targets[test_step.id] = step_result
            continue

        hook = hooks[test_step.hook_id]
        hook_name = hook.name or "Before"
        lowered_hook_name = hook_name.lower()
        if lowered_hook_name.startswith("before"):
            fixture_group = before_fixtures
        elif lowered_hook_name.startswith("after"):
            fixture_group = after_fixtures
        else:
            raise AllureConversionError(
                f"hook {hook.id!r} has unsupported name {hook_name!r}; expected a Before or After hook"
            )
        fixture: dict[str, Any] = {
            "uuid": str(uuid4()),
            "name": hook_name,
            "status": status,
            "stage": "finished",
            "start": _timestamp_millis(started.timestamp),
            "stop": _timestamp_millis(finished.timestamp),
        }
        if details:
            fixture["statusDetails"] = details
            if status != "passed":
                status_details_candidates.append((status, details))
        fixture_group.append(fixture)
        step_targets[test_step.id] = fixture

    (
        scenario_name,
        labels,
        parameters,
        description,
        full_name,
        test_case_id,
        history_id,
    ) = _scenario_metadata(envelopes, pickle)
    scenario_status = _scenario_status(tuple(statuses))
    result_uuid = str(uuid4())
    result: dict[str, Any] = {
        "uuid": result_uuid,
        "name": scenario_name,
        "fullName": full_name,
        "testCaseId": test_case_id,
        "historyId": history_id,
        "status": scenario_status,
        "stage": "finished",
        "start": _timestamp_millis(case_started.timestamp),
        "stop": _timestamp_millis(case_finished.timestamp),
        "steps": scenario_steps,
        "labels": labels,
        "parameters": parameters,
    }
    if description:
        result["description"] = description
    if status_details_candidates:
        result["statusDetails"] = max(
            status_details_candidates,
            key=lambda candidate: _status_priority(candidate[0]),
        )[1]

    attachment_files = _materialize_attachments(
        envelopes,
        attempt_id,
        case_started_position,
        case_finished_position,
        step_event_positions,
        step_targets,
        result,
    )
    container = {
        "uuid": str(uuid4()),
        "children": [result_uuid],
        "befores": before_fixtures,
        "afters": after_fixtures,
    }
    return result, container, attachment_files


def _step_message(
    envelopes: list[messages.Envelope], kind: str, attempt_id: str, step_id: str
) -> Any:
    for message in _messages(envelopes, kind):
        if message.test_case_started_id == attempt_id and message.test_step_id == step_id:
            return message
    raise AllureConversionError(f"missing {kind.replace('_', ' ')} for attempt {attempt_id!r}, step {step_id!r}")


def _status_details(test_step_result: messages.TestStepResult, stack_trace: str | None) -> dict[str, str]:
    details: dict[str, str] = {}
    exception = test_step_result.exception
    result_message = test_step_result.message
    if stack_trace is None and exception is not None:
        stack_trace = getattr(exception, "stack_trace", None)
    if exception is not None:
        messages: list[str] = []
        for message in (exception.message, result_message):
            if message and message not in messages:
                messages.append(message)
        if messages:
            details["message"] = "\n\n".join(messages)
    elif result_message:
        details["message"] = result_message
    if stack_trace is not None:
        details["trace"] = stack_trace
    return details


def _materialize_attachments(
    envelopes: list[messages.Envelope],
    attempt_id: str,
    case_started_position: int,
    case_finished_position: int,
    step_event_positions: dict[str, tuple[int, int]],
    step_targets: dict[str, dict[str, Any]],
    result: dict[str, Any],
) -> list[tuple[str, bytes]]:
    files: list[tuple[str, bytes]] = []
    for position, envelope in enumerate(envelopes):
        attachment = envelope.attachment
        if attachment is None:
            continue
        if attachment.test_case_started_id != attempt_id:
            continue

        test_step_id = attachment.test_step_id
        attachment_target: dict[str, Any]
        if test_step_id is None:
            if not case_started_position < position < case_finished_position:
                raise AllureConversionError("scenario attachment is outside the active scenario lifecycle")
            attachment_target = result
        else:
            step_positions = step_event_positions.get(test_step_id)
            if step_positions is None:
                raise AllureConversionError(
                    f"attachment {attachment.file_name or '<unnamed>'!r} refers to unknown test step {test_step_id!r}"
                )
            if not step_positions[0] < position < step_positions[1]:
                raise AllureConversionError(
                    f"attachment {attachment.file_name or '<unnamed>'!r} is outside test step {test_step_id!r}"
                )
            step_target = step_targets.get(test_step_id)
            if step_target is None:
                raise AllureConversionError(
                    f"attachment {attachment.file_name or '<unnamed>'!r} refers to an unsupported test step "
                    f"{test_step_id!r}"
                )
            attachment_target = step_target

        _materialize_attachment(attachment, attachment_target, files)
    return files


def _materialize_unscoped_attachments(
    envelopes: list[messages.Envelope],
    converted: list[tuple[dict[str, Any], dict[str, Any]]],
    files: list[tuple[str, bytes]],
    results_by_case_id: dict[str, list[dict[str, Any]]],
) -> None:
    """Attach no-attempt messages to their case or mark them as a run fallback."""
    for envelope in envelopes:
        attachment = envelope.attachment
        if (
            attachment is None
            or attachment.test_case_started_id is not None
            or attachment.test_run_hook_started_id is not None
        ):
            continue
        case_id = _attachment_case_id(attachment)
        fallback_label: str | None = None
        if case_id is not None:
            results = results_by_case_id.get(case_id)
            if not results:
                if not converted:
                    raise AllureConversionError(
                        f"cannot preserve attachment {attachment.file_name or '<unnamed>'!r} for "
                        f"unmapped testCaseId {case_id!r} without a completed scenario"
                    )
                results = [converted[0][0]]
                fallback_label = f"Cucumber unmapped testCaseId {case_id!r} fallback"
        elif converted:
            results = [converted[0][0]]
            fallback_label = "Cucumber run-level fallback"
        else:
            raise AllureConversionError("cannot attach unscoped Cucumber attachments without a completed scenario")

        for result in results:
            _materialize_attachment(attachment, result, files, fallback_label=fallback_label)


def _materialize_attachment(
    attachment: messages.Attachment,
    target: dict[str, Any],
    files: list[tuple[str, bytes]],
    *,
    fallback_label: str | None = None,
) -> None:
    attachment_id = str(uuid4())
    source = f"attachments/{attachment_id}.attach"
    name = _safe_attachment_name(attachment.file_name, attachment_id)
    if fallback_label is not None:
        name = f"{fallback_label}: {name}"
    target.setdefault("attachments", []).append(
        {
            "name": name,
            "source": source,
            "type": attachment.media_type,
        }
    )
    files.append((source, _attachment_bytes(attachment)))


def _attachment_case_id(attachment: messages.Attachment) -> str | None:
    """Read a case correlation id from an optional JSON extension attachment body."""
    if attachment.media_type != "application/json" and not attachment.media_type.endswith("+json"):
        return None
    try:
        metadata = json.loads(attachment.body)
    except (TypeError, ValueError):
        return None
    if not isinstance(metadata, dict):
        return None
    case_id = metadata.get("testCaseId")
    return case_id if isinstance(case_id, str) and case_id else None


def _safe_attachment_name(file_name: str | None, attachment_id: str) -> str:
    if file_name is None:
        return f"attachment-{attachment_id}"
    if (
        not file_name
        or file_name in {".", ".."}
        or "\x00" in file_name
        or "/" in file_name
        or "\\" in file_name
        or ".." in PurePosixPath(file_name).parts
        or PurePosixPath(file_name).is_absolute()
        or PureWindowsPath(file_name).drive
        or PureWindowsPath(file_name).is_absolute()
    ):
        raise AllureConversionError(f"unsafe attachment file name: {file_name!r}")
    return file_name


def _attachment_bytes(attachment: messages.Attachment) -> bytes:
    encoding = getattr(attachment.content_encoding, "value", attachment.content_encoding)
    if encoding == "IDENTITY":
        return attachment.body.encode("utf-8")
    if encoding == "BASE64":
        try:
            return b64decode(attachment.body, validate=True)
        except ValueError as exc:
            raise AllureConversionError(
                f"attachment {attachment.file_name or '<unnamed>'!r} has malformed BASE64 content"
            ) from exc
    raise AllureConversionError(
        f"attachment {attachment.file_name or '<unnamed>'!r} has unsupported content encoding {encoding!r}"
    )


def _attach_raw_extensions(
    converted: list[tuple[dict[str, Any], dict[str, Any]]],
    attachments: list[tuple[str, bytes]],
    raw_extensions: list[bytes],
) -> None:
    """Attach unknown run-level envelopes after the known run has validated."""
    if not raw_extensions:
        return
    if not converted:
        raise AllureConversionError("cannot attach unknown Cucumber messages without a completed scenario")

    first_result = converted[0][0]
    for index, raw_json in enumerate(raw_extensions, start=1):
        attachment_id = str(uuid4())
        source = f"attachments/{attachment_id}.attach"
        first_result.setdefault("attachments", []).append(
            {
                "name": f"Cucumber extension {index}",
                "source": source,
                "type": "application/json",
            }
        )
        attachments.append((source, raw_json))


def _attach_run_diagnostics(
    converted: list[tuple[dict[str, Any], dict[str, Any]]],
    attachments: list[tuple[str, bytes]],
    run_finished: Any,
    raw_stack_trace: str | None,
) -> None:
    """Attach run-level diagnostics without changing scenario outcome statuses."""
    message = run_finished.message
    exception = run_finished.exception
    success = run_finished.success
    if success and message is None and exception is None:
        return
    if not converted:
        raise AllureConversionError("cannot attach run diagnostics without a completed scenario")

    diagnostics: dict[str, Any] = {"success": success}
    if message is not None:
        diagnostics["message"] = message
    if exception is not None:
        exception_data: dict[str, str] = {"type": exception.type}
        if exception.message is not None:
            exception_data["message"] = exception.message
        if raw_stack_trace is not None:
            exception_data["stackTrace"] = raw_stack_trace
        diagnostics["exception"] = exception_data

    source = f"attachments/{uuid4()}.attach"
    converted[0][0].setdefault("attachments", []).append(
        {
            "name": "Cucumber test run diagnostics",
            "source": source,
            "type": "application/json",
        }
    )
    attachments.append((source, _json_bytes(diagnostics)))


def _render_artifacts(
    converted: list[tuple[dict[str, Any], dict[str, Any]]],
    attachments: list[tuple[str, bytes]],
    run_hook_container: dict[str, Any] | None = None,
) -> list[tuple[str, bytes]]:
    """Serialize every output file in memory before the destination is changed."""
    artifacts = list(attachments)
    for result, container in converted:
        artifacts.append((f"{result['uuid']}-result.json", _json_bytes(result)))
        artifacts.append((f"{container['uuid']}-container.json", _json_bytes(container)))
    if run_hook_container is not None:
        artifacts.append((f"{run_hook_container['uuid']}-container.json", _json_bytes(run_hook_container)))
    return _validate_artifacts(artifacts)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    try:
        return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise AllureConversionError(f"cannot serialize Allure result: {exc}") from exc


def _validate_artifacts(artifacts: list[tuple[str, bytes]]) -> list[tuple[str, bytes]]:
    validated: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    paths: list[PurePosixPath] = []
    for source, content in artifacts:
        relative = _safe_relative_output_path(source)
        normalized = relative.as_posix()
        if normalized in seen:
            raise AllureConversionError(f"duplicate Allure output path: {source!r}")
        seen.add(normalized)
        paths.append(relative)
        if not isinstance(content, bytes):
            raise AllureConversionError(f"Allure output for {source!r} is not bytes")
        validated.append((normalized, content))

    for index, first in enumerate(paths):
        for second in paths[index + 1 :]:
            if first in second.parents or second in first.parents:
                raise AllureConversionError(
                    f"conflicting Allure output paths: {first.as_posix()!r} and {second.as_posix()!r}"
                )
    return validated


def _safe_relative_output_path(source: str) -> PurePosixPath:
    if (
        not source
        or "\x00" in source
        or "\\" in source
        or PureWindowsPath(source).drive
        or PureWindowsPath(source).is_absolute()
    ):
        raise AllureConversionError(f"unsafe Allure output path: {source!r}")
    relative = PurePosixPath(source)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.as_posix() != source
    ):
        raise AllureConversionError(f"unsafe Allure output path: {source!r}")
    if relative.parts[0] == "attachments" and len(relative.parts) < 2:
        raise AllureConversionError(f"unsafe Allure attachment path: {source!r}")
    return relative


def _write_artifacts_transactionally(output_dir: Path, artifacts: list[tuple[str, bytes]]) -> None:
    """Install a complete set of files, restoring prior files if any replacement fails."""
    validated = _validate_artifacts(artifacts)
    root = Path(os.path.abspath(output_dir))
    _validate_output_root(root)
    staging_parent = _nearest_existing_directory(root.parent)

    try:
        with tempfile.TemporaryDirectory(prefix=".allure-stage-", dir=staging_parent) as temporary:
            stage_root = Path(temporary)
            staged_root = stage_root / "staged"
            for source, content in validated:
                staged_file = staged_root.joinpath(*PurePosixPath(source).parts)
                staged_file.parent.mkdir(parents=True, exist_ok=True)
                staged_file.write_bytes(content)

            _validate_output_root(root)
            for source, _content in validated:
                _validate_target(root.joinpath(*PurePosixPath(source).parts), root, source)
            created_directories: list[Path] = []
            replacements: list[dict[str, Any]] = []
            try:
                for source, _content in validated:
                    target = root.joinpath(*PurePosixPath(source).parts)
                    _make_directories(target.parent, created_directories)
                    _validate_target(target, root, source)

                    replacement: dict[str, Any] = {
                        "target": target,
                        "backup": None,
                        "installed": False,
                    }
                    backup = stage_root / "backups" / PurePosixPath(source)
                    if target.exists():
                        backup.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(target, backup)
                        replacement["backup"] = backup
                    replacements.append(replacement)
                    staged_file = staged_root.joinpath(*PurePosixPath(source).parts)
                    os.replace(staged_file, target)
                    replacement["installed"] = True
            except BaseException as exc:
                rollback_errors = _rollback_replacements(replacements, created_directories)
                if rollback_errors:
                    details = "; ".join(str(error) for error in rollback_errors)
                    raise AllureConversionError(
                        f"failed to write Allure results and rollback was incomplete: {details}"
                    ) from exc
                raise
    except AllureConversionError:
        raise
    except OSError as exc:
        raise AllureConversionError(f"cannot write Allure results to {output_dir}: {exc}") from exc


def _validate_output_root(root: Path) -> None:
    if "\x00" in str(root):
        raise AllureConversionError(f"unsafe Allure output directory: {str(root)!r}")
    current = Path(root.anchor)
    for part in root.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise AllureConversionError(f"Allure output path must not contain symlinks: {current}")
        if current.exists() and not current.is_dir():
            raise AllureConversionError(f"Allure output path component is not a directory: {current}")


def _nearest_existing_directory(path: Path) -> Path:
    current = path
    while not current.exists():
        if current == current.parent:
            raise AllureConversionError(f"cannot find an existing parent directory for {path}")
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise AllureConversionError(f"Allure staging parent must be a non-symlink directory: {current}")
    return current


def _make_directories(path: Path, created_directories: list[Path]) -> None:
    missing: list[Path] = []
    current = path
    while not current.exists():
        if current == current.parent:
            raise AllureConversionError(f"cannot create Allure output directory: {path}")
        missing.append(current)
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise AllureConversionError(f"Allure output parent must be a non-symlink directory: {current}")
    for directory in reversed(missing):
        directory.mkdir()
        created_directories.append(directory)


def _validate_target(target: Path, root: Path, source: str) -> None:
    current = target.parent
    while current != root.parent:
        if current.is_symlink() or (current.exists() and not current.is_dir()):
            raise AllureConversionError(f"unsafe Allure output directory for {source!r}: {current}")
        if current == root:
            break
        current = current.parent
    if target.is_symlink():
        raise AllureConversionError(f"Allure output target must not be a symlink: {source!r}")
    if target.exists() and not target.is_file():
        raise AllureConversionError(f"Allure output target is not a regular file: {source!r}")
    try:
        target.parent.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise AllureConversionError(f"Allure output path escapes the result directory: {source!r}") from exc


def _rollback_replacements(
    replacements: list[dict[str, Any]], created_directories: list[Path]
) -> list[OSError]:
    errors: list[OSError] = []
    for replacement in reversed(replacements):
        target: Path = replacement["target"]
        backup: Path | None = replacement["backup"]
        if replacement["installed"] and (target.exists() or target.is_symlink()):
            try:
                target.unlink()
            except OSError as exc:
                errors.append(exc)
        if backup is not None and backup.exists():
            try:
                os.replace(backup, target)
            except OSError as exc:
                errors.append(exc)
    for directory in reversed(created_directories):
        try:
            directory.rmdir()
        except OSError as exc:
            if exc.errno not in {errno.ENOTEMPTY, errno.ENOENT}:
                errors.append(exc)
    return errors


def _scenario_metadata(
    envelopes: list[messages.Envelope], pickle: messages.Pickle
) -> tuple[str, list[dict[str, str]], list[dict[str, str]], str | None, str, str, str]:
    labels = [{"name": "tag", "value": tag.name} for tag in pickle.tags]
    documents: list[messages.GherkinDocument] = _messages(envelopes, "gherkin_document")
    scenario: messages.Scenario | None = None
    scenario_document: messages.GherkinDocument | None = None
    scenario_rule: Any | None = None
    if pickle.ast_node_ids:
        scenario_id = pickle.ast_node_ids[0]
        for document in documents:
            if document is None:
                continue
            if document.feature is None:
                continue
            for child in document.feature.children:
                if child.scenario is not None and child.scenario.id == scenario_id:
                    candidate = child.scenario
                    if scenario is None:
                        scenario, scenario_document, scenario_rule = candidate, document, None
                    if document.uri == pickle.uri:
                        scenario, scenario_document, scenario_rule = candidate, document, None
                        break
                if child.rule is not None:
                    for rule_child in child.rule.children:
                        if rule_child.scenario is not None and rule_child.scenario.id == scenario_id:
                            candidate = rule_child.scenario
                            if scenario is None:
                                scenario, scenario_document, scenario_rule = candidate, document, child.rule
                            if document.uri == pickle.uri:
                                scenario, scenario_document, scenario_rule = candidate, document, child.rule
                                break
            if scenario is not None and scenario_document is document and document.uri == pickle.uri:
                break

    source_uri = _normalize_source_uri((scenario_document.uri if scenario_document is not None else "") or pickle.uri)
    if scenario is None:
        title = pickle.name
        full_name = _qualify_identity(source_uri, title)
        test_case_id = _qualify_identity(source_uri, title)
        history_id = _history_id(test_case_id, [])
        return title, labels, [], None, full_name, test_case_id, history_id

    labels = _scenario_tag_labels(
        pickle,
        scenario,
        feature=scenario_document.feature if scenario_document is not None else None,
        rule=scenario_rule,
    )

    parameters: list[dict[str, str]] = []
    if len(pickle.ast_node_ids) > 1:
        row_id = pickle.ast_node_ids[-1]
        for example in scenario.examples:
            if example.table_header is None:
                continue
            row = next((row for row in example.table_body if row.id == row_id), None)
            if row is None:
                continue
            if len(example.table_header.cells) != len(row.cells):
                raise AllureConversionError(f"outline row {row_id!r} does not match its Examples header")
            parameters = [
                {"name": header.value, "value": cell.value}
                for header, cell in zip(example.table_header.cells, row.cells, strict=True)
            ]
            break
        if not parameters:
            raise AllureConversionError(f"could not match outline row {row_id!r} to its Examples table")

    values = {parameter["name"]: parameter["value"] for parameter in parameters}
    name = re.sub(r"<([^<>]+)>", lambda match: values.get(match.group(1), match.group(0)), scenario.name)
    full_name = _qualify_identity(source_uri, scenario.name)
    location = scenario.location
    source_position = f"{location.line}:{location.column}" if location is not None else scenario.name
    test_case_id = _qualify_identity(source_uri, f"{source_position}:{scenario.name}")
    history_id = _history_id(test_case_id, parameters)
    return name, labels, parameters, scenario.description or None, full_name, test_case_id, history_id


def _normalize_source_uri(uri: str) -> str:
    normalized = PurePosixPath(uri.replace("\\", "/")).as_posix()
    return "" if normalized == "." else normalized


def _qualify_identity(source_uri: str, scenario_identity: str) -> str:
    return f"{source_uri}:{scenario_identity}" if source_uri else scenario_identity


def _history_id(test_case_id: str, parameters: list[dict[str, str]]) -> str:
    identity = json.dumps(
        {"testCaseId": test_case_id, "parameters": parameters},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.md5(identity.encode("utf-8")).hexdigest()


def _scenario_tag_labels(
    pickle: messages.Pickle, scenario: Any, *, feature: Any = None, rule: Any = None
) -> list[dict[str, str]]:
    """Use Gherkin tags for each scenario ancestor while retaining Pickle tags."""
    gherkin_tags = {tag.id: tag for tag in scenario.tags}
    pickle_tag_ids: set[str] = set()
    labels: list[dict[str, str]] = []
    for tag in pickle.tags:
        pickle_tag_ids.add(tag.ast_node_id)
        source_tag = gherkin_tags.get(tag.ast_node_id)
        labels.append({"name": "tag", "value": source_tag.name if source_tag is not None else tag.name})
    labels.extend(
        {"name": "tag", "value": tag.name} for tag_id, tag in gherkin_tags.items() if tag_id not in pickle_tag_ids
    )
    for node in (feature, rule):
        for tag in getattr(node, "tags", ()):
            tag_id = getattr(tag, "id", None)
            if isinstance(tag_id, str) and tag_id in pickle_tag_ids:
                continue
            labels.append({"name": "tag", "value": tag.name})
    return labels


def _pickle_step_argument_presentation(pickle_step: Any) -> dict[str, Any] | None:
    argument = pickle_step.argument
    if argument is None:
        return None
    if argument.doc_string is not None:
        doc_string = argument.doc_string
        content = doc_string.content
        description = f"{doc_string.media_type or ''}\n\n{content}"
        return {
            "description": description,
            "descriptionHtml": description,
            "parameters": [{"name": "docString", "value": content}],
        }
    if argument.data_table is not None:
        data_table = "\n".join(
            f"| {' | '.join(cell.value for cell in row.cells)} |" for row in argument.data_table.rows
        )
        return {
            "description": data_table,
            "descriptionHtml": data_table,
            "parameters": [{"name": "dataTable", "value": data_table}],
        }
    return None


def _timestamp_nanos(timestamp: messages.Timestamp) -> int:
    return timestamp.seconds * 1_000_000_000 + timestamp.nanos


def _timestamp_millis(timestamp: messages.Timestamp) -> int:
    return timestamp.seconds * 1_000 + timestamp.nanos // 1_000_000


def _allure_status(status: str) -> str:
    return {
        "PASSED": "passed",
        "FAILED": "failed",
        "SKIPPED": "skipped",
        "UNDEFINED": "broken",
        "AMBIGUOUS": "broken",
        "PENDING": "broken",
        "UNKNOWN": "unknown",
        "UNTESTED": "unknown",
    }.get(status, "broken")


def _status_priority(status: str) -> int:
    return {"failed": 3, "broken": 2, "unknown": 1}.get(status, 0)


def _scenario_status(statuses: tuple[str, ...]) -> str:
    for status in ("failed", "broken", "unknown", "skipped"):
        if status in statuses:
            return status
    return "passed"


__all__ = ["AllureConversionError", "convert_allure_messages"]
