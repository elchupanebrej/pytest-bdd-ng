"""Convert a complete Cucumber Messages stream to standalone Allure files."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import tempfile
from base64 import b64decode
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from pydantic import ValidationError

from pytest_cuke.model.message_converter import envelope_from_dict
from pytest_cuke.model.message_extension import PAYLOAD_KINDS, get_payload_kind

if TYPE_CHECKING:
    import messages


class AllureConversionError(Exception):
    """An input stream cannot be converted to Allure results."""


def convert_allure_messages(input_path: Path, output_dir: Path) -> None:
    """Convert every completed scenario attempt in one Cucumber Messages run."""
    envelopes, exception_traces, raw_extensions = _read_envelopes(input_path)
    converted, attachments = _convert_scenarios(envelopes, exception_traces)
    _attach_raw_extensions(converted, attachments, raw_extensions)
    artifacts = _render_artifacts(converted, attachments)

    try:
        _write_artifacts_transactionally(output_dir, artifacts)
    except AllureConversionError:
        raise
    except OSError as exc:
        raise AllureConversionError(f"cannot write Allure results to {output_dir}: {exc}") from exc


def _read_envelopes(
    input_path: Path,
) -> tuple[list[messages.Envelope], dict[tuple[str, str], str], list[bytes]]:
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
    raw_extensions: list[bytes] = []
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
        validation_payload, stack_trace = _without_exception_stack_trace(payload)
        try:
            envelope = envelope_from_dict(validation_payload)
        except (TypeError, ValueError, ValidationError) as exc:
            detail = _validation_summary(exc)
            raise AllureConversionError(
                f"invalid Cucumber message in {input_path} at line {line_number}: {detail}"
            ) from exc
        envelopes.append(envelope)
        if stack_trace is not None:
            if envelope.test_step_finished is None:
                raise AllureConversionError(
                    f"exception stack trace in {input_path} at line {line_number} has no test step"
                )
            key = (envelope.test_step_finished.test_case_started_id, envelope.test_step_finished.test_step_id)
            if key in exception_traces:
                raise AllureConversionError(f"duplicate exception stack trace in {input_path} at line {line_number}")
            exception_traces[key] = stack_trace

    if not envelopes:
        raise AllureConversionError(f"input contains no Cucumber messages: {input_path}")
    return envelopes, exception_traces, raw_extensions


def _known_payload_names() -> set[str]:
    names = set(PAYLOAD_KINDS)
    names.update(_camel_payload_name(kind) for kind in PAYLOAD_KINDS)
    return names


def _camel_payload_name(kind: str) -> str:
    first, *rest = kind.split("_")
    return first + "".join(part.title() for part in rest)


def _without_exception_stack_trace(payload: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Keep schema-valid stackTrace data despite the older generated messages model."""
    test_step_finished = payload.get("testStepFinished")
    if not isinstance(test_step_finished, dict):
        return payload, None
    test_step_result = test_step_finished.get("testStepResult")
    if not isinstance(test_step_result, dict):
        return payload, None
    exception = test_step_result.get("exception")
    if not isinstance(exception, dict) or "stackTrace" not in exception:
        return payload, None
    stack_trace = exception.get("stackTrace")
    if not isinstance(stack_trace, str):
        raise AllureConversionError("Cucumber exception stackTrace must be a string")

    validation_payload = dict(payload)
    validation_step_finished = dict(test_step_finished)
    validation_result = dict(test_step_result)
    validation_exception = dict(exception)
    del validation_exception["stackTrace"]
    validation_result["exception"] = validation_exception
    validation_step_finished["testStepResult"] = validation_result
    validation_payload["testStepFinished"] = validation_step_finished
    return validation_payload, stack_trace


def _validation_summary(error: Exception) -> str:
    if isinstance(error, ValidationError):
        details = error.errors()
        return "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}" for item in details
        )
    return str(error)


def _convert_scenarios(
    envelopes: list[messages.Envelope], exception_traces: dict[tuple[str, str], str]
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[tuple[str, bytes]]]:
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
        attachment_files.extend(files)
    return converted, attachment_files


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
        if envelope.attachment is not None and envelope.attachment.test_case_started_id not in known_attempt_ids:
            raise AllureConversionError(
                f"attachment {envelope.attachment.file_name or '<unnamed>'!r} refers to unknown attempt "
                f"{envelope.attachment.test_case_started_id!r}"
            )
    return attempts


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
    message = test_step_result.message or (exception.message if exception is not None else None)
    if message:
        details["message"] = message
    if stack_trace is None and exception is not None:
        stack_trace = getattr(exception, "stack_trace", None)
    if stack_trace:
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

        attachment_id = str(uuid4())
        name = _safe_attachment_name(attachment.file_name, attachment_id)
        source = f"attachments/{attachment_id}.attach"
        reference = {"name": name, "source": source, "type": attachment.media_type}
        attachment_target.setdefault("attachments", []).append(reference)
        files.append((source, _attachment_bytes(attachment)))
    return files


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


def _render_artifacts(
    converted: list[tuple[dict[str, Any], dict[str, Any]]],
    attachments: list[tuple[str, bytes]],
) -> list[tuple[str, bytes]]:
    """Serialize every output file in memory before the destination is changed."""
    artifacts = list(attachments)
    for result, container in converted:
        artifacts.append((f"{result['uuid']}-result.json", _json_bytes(result)))
        artifacts.append((f"{container['uuid']}-container.json", _json_bytes(container)))
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
                        scenario, scenario_document = candidate, document
                    if document.uri == pickle.uri:
                        scenario, scenario_document = candidate, document
                        break
                if child.rule is not None:
                    for rule_child in child.rule.children:
                        if rule_child.scenario is not None and rule_child.scenario.id == scenario_id:
                            candidate = rule_child.scenario
                            if scenario is None:
                                scenario, scenario_document = candidate, document
                            if document.uri == pickle.uri:
                                scenario, scenario_document = candidate, document
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

    labels = _scenario_tag_labels(pickle, scenario)

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


def _scenario_tag_labels(pickle: messages.Pickle, scenario: Any) -> list[dict[str, str]]:
    """Use Gherkin tags for scenario tags while retaining inherited Pickle tags."""
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
