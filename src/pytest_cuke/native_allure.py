"""Consume validated Cucumber Messages and write native Allure results live."""

from __future__ import annotations

import base64
import binascii
import json
import mimetypes
import os
import re
import time
import traceback
from contextlib import suppress
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import pytest

from pytest_cuke.allure_conversion import (
    AllureConversionError,
    _allure_status,
    _attachment_bytes,
    _attachment_case_id,
    _pickle_step_argument_presentation,
    _safe_attachment_name,
    _scenario_metadata,
    _scenario_status,
    _status_details,
    _status_priority,
    _timestamp_millis,
)
from pytest_cuke.allure_status import _allure_api_step_status
from pytest_cuke.model.message_consolidation import LiveMessageAdapter
from pytest_cuke.model.message_extension import get_payload_kind
from pytest_cuke.model.message_registry import EnvelopeRegistry
from pytest_cuke.model.message_types import Envelope, message_from_dict, message_to_dict

if TYPE_CHECKING:
    from pytest import Config

    from pytest_cuke.model import message_types as messages


_NATIVE_API_STEP_MEDIA_TYPE = "application/vnd.pytest-cuke.allure-api-step+json"
_NATIVE_API_ATTACHMENT_MEDIA_TYPE = "application/vnd.pytest-cuke.allure-api-attachment+json"


class NativeAllureDependencyError(RuntimeError):
    """The optional Allure runtime is required for native reporting."""


@dataclass(slots=True)
class _ActiveStep:
    uuid: str
    kind: str


@dataclass(slots=True)
class _ActiveCase:
    test_case: messages.TestCase
    pickle: messages.Pickle
    result_uuid: str
    container_uuid: str
    step_uuids: dict[str, _ActiveStep] = field(default_factory=dict)
    statuses: list[str] = field(default_factory=list)
    failures: list[tuple[str, dict[str, str]]] = field(default_factory=list)
    active_step_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class _ActiveRunHook:
    fixture_uuid: str
    kind: str


class NativeAllureReporter:
    """Map the live Messages stream to allure-python-commons lifecycle objects."""

    def __init__(self, output_dir: Path) -> None:
        try:
            allure_commons = import_module("allure_commons")
            lifecycle_module = import_module("allure_commons.lifecycle")
            logger_module = import_module("allure_commons.logger")
            model2 = import_module("allure_commons.model2")
        except ImportError as error:
            raise NativeAllureDependencyError(
                "native Allure reporting requires the optional dependency; install pytest-cuke[allure]"
            ) from error

        self.output_dir = Path(os.path.expandvars(os.path.expanduser(str(output_dir)))).resolve()
        self._allure_commons = allure_commons
        self._lifecycle = lifecycle_module.AllureLifecycle()
        self._file_logger = logger_module.AllureFileLogger(str(self.output_dir))
        self._asdict = logger_module.asdict
        self._allure_indent = logger_module.INDENT
        self._model = {
            "Label": model2.Label,
            "Parameter": model2.Parameter,
            "Status": model2.Status,
            "StatusDetails": model2.StatusDetails,
            "TestAfterResult": model2.TestAfterResult,
        }
        self._live_adapter = LiveMessageAdapter()
        self._registry = EnvelopeRegistry()
        self._test_cases: dict[str, messages.TestCase] = {}
        self._pickles: dict[str, messages.Pickle] = {}
        self._hooks: dict[str, messages.Hook] = {}
        self._active_cases: dict[str, _ActiveCase] = {}
        self._cases_by_attempt: dict[str, _ActiveCase] = {}
        self._active_run_hooks: dict[str, _ActiveRunHook] = {}
        self._session_container_uuid: str | None = None
        self._session_children: list[str] = []
        self._case_result_uuids: dict[str, list[str]] = {}
        self._pending_case_attachments: dict[str, list[messages.Attachment]] = {}
        self._pending_run_attachments: list[tuple[messages.Attachment, str | None]] = []
        self._first_result_uuid: str | None = None
        self._api_hooks: object | None = None
        self._api_step_uuids: dict[str, str] = {}
        self._api_step_stack: list[tuple[str, str]] = []
        self._test_run_finished_seen = False
        self._session_container_reported = False
        self._started = False

    def start(self) -> None:
        """Create the destination and register hooks for the Allure public API."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._api_hooks = self._make_api_hooks()
        self._allure_commons.plugin_manager.register(self._api_hooks)
        self._started = True

    def stop(self) -> None:
        """Unregister reporting hooks after pytest has finished emitting Messages."""
        if not self._started:
            return
        try:
            if not self._test_run_finished_seen:
                self._finish_partial_session()
        finally:
            if self._api_hooks is not None:
                self._allure_commons.plugin_manager.unregister(self._api_hooks)
                self._api_hooks = None
            self._started = False

    @pytest.hookimpl
    def pytest_cuke_message_validated(self, config: Config, message: Envelope) -> None:
        """Consume one controller envelope after stream validation."""
        del config
        payload = message_to_dict(message)
        normalized = self._live_adapter.controller_envelope(payload)
        if normalized is None:
            return
        envelope = message if normalized == payload else message_from_dict(normalized, Envelope)
        self._consume(envelope, normalized)

    @pytest.hookimpl
    def pytest_cuke_message_batch(self, config: Config, batch: dict[str, Any]) -> None:
        """Consume normalized worker envelopes forwarded to the xdist controller."""
        del config
        worker_id = batch.get("worker_id")
        raw_envelopes = batch.get("envelopes")
        if not isinstance(worker_id, str) or not worker_id or not isinstance(raw_envelopes, list):
            raise AllureConversionError("received an invalid pytest-cuke xdist Messages batch")
        for raw_envelope in raw_envelopes:
            if not isinstance(raw_envelope, dict):
                raise AllureConversionError("received a non-object envelope in a pytest-cuke xdist batch")
            normalized = self._live_adapter.worker_envelope(raw_envelope, worker_id=worker_id)
            if normalized is None:
                continue
            self._consume(message_from_dict(normalized, Envelope), normalized)

    def _consume(self, envelope: Envelope, wire: dict[str, Any]) -> None:
        kind = get_payload_kind(envelope)
        if kind is None:
            return
        self._registry.add_envelope(envelope)
        if kind == "pickle":
            self._pickles[cast("messages.Pickle", envelope.pickle).id] = cast("messages.Pickle", envelope.pickle)
        elif kind == "test_case":
            test_case = cast("messages.TestCase", envelope.test_case)
            self._test_cases[test_case.id] = test_case
        elif kind == "hook":
            hook = cast("messages.Hook", envelope.hook)
            self._hooks[hook.id] = hook
        elif kind == "test_run_started":
            self._start_session_container(cast("messages.TestRunStarted", envelope.test_run_started))
        elif kind == "test_run_hook_started":
            self._start_run_hook(cast("messages.TestRunHookStarted", envelope.test_run_hook_started))
        elif kind == "test_run_hook_finished":
            self._finish_run_hook(cast("messages.TestRunHookFinished", envelope.test_run_hook_finished), wire)
        elif kind == "test_case_started":
            self._start_case(cast("messages.TestCaseStarted", envelope.test_case_started))
        elif kind == "test_step_started":
            self._start_step(cast("messages.TestStepStarted", envelope.test_step_started))
        elif kind == "test_step_finished":
            self._finish_step(cast("messages.TestStepFinished", envelope.test_step_finished), wire)
        elif kind == "test_case_finished":
            self._finish_case(cast("messages.TestCaseFinished", envelope.test_case_finished))
        elif kind == "attachment":
            self._attach(cast("messages.Attachment", envelope.attachment))
        elif kind == "test_run_finished":
            self._test_run_finished_seen = True
            self._finish_session(cast("messages.TestRunFinished", envelope.test_run_finished), wire)

    def _start_session_container(self, run_started: messages.TestRunStarted) -> None:
        if self._session_container_uuid is not None:
            return
        container_uuid = str(uuid4())
        self._session_container_uuid = container_uuid
        with self._lifecycle.start_container(uuid=container_uuid) as container:
            container.name = "Test session"
            container.start = _timestamp_millis(run_started.timestamp)

    def _start_case(self, started: messages.TestCaseStarted) -> None:
        test_case = self._test_cases.get(started.test_case_id)
        if test_case is None:
            raise AllureConversionError(f"test case start refers to unknown test case {started.test_case_id!r}")
        pickle = self._pickles.get(test_case.pickle_id)
        if pickle is None:
            raise AllureConversionError(f"test case {test_case.id!r} refers to unknown pickle {test_case.pickle_id!r}")
        if started.id in self._active_cases:
            raise AllureConversionError(f"duplicate active test case attempt {started.id!r}")

        name, tags, parameters, _description, full_name, test_case_id, history_id = _scenario_metadata(
            self._registry.envelopes, pickle
        )
        feature, rule, scenario = self._gherkin_identity(pickle)
        feature_name = getattr(feature, "name", None)
        rule_name = getattr(rule, "name", None)
        scenario_name = getattr(scenario, "name", None)
        description_parts = [
            str(value).strip()
            for value in (
                getattr(feature, "description", None),
                getattr(rule, "description", None),
                getattr(scenario, "description", None),
            )
            if isinstance(value, str) and value.strip()
        ]
        result_uuid = str(uuid4())
        container_uuid = str(uuid4())
        start = _timestamp_millis(started.timestamp)
        case = _ActiveCase(
            test_case=test_case,
            pickle=pickle,
            result_uuid=result_uuid,
            container_uuid=container_uuid,
        )
        with self._lifecycle.schedule_test_case(result_uuid) as result:
            result.name = name
            result.fullName = full_name
            result.testCaseId = test_case_id
            result.historyId = history_id
            result.start = start
            result.stage = "running"
            result.description = "\n\n".join(description_parts) or None
            result.titlePath = [value for value in (feature_name, rule_name, name) if isinstance(value, str) and value]
            result.labels.extend(self._model["Label"](name=label["name"], value=label["value"]) for label in tags)
            if isinstance(feature_name, str) and feature_name:
                result.labels.append(self._model["Label"](name="feature", value=feature_name))
                result.labels.append(self._model["Label"](name="parentSuite", value=feature_name))
            if isinstance(rule_name, str) and rule_name:
                result.labels.append(self._model["Label"](name="rule", value=rule_name))
                result.labels.append(self._model["Label"](name="suite", value=rule_name))
            if isinstance(scenario_name, str) and scenario_name:
                result.labels.append(self._model["Label"](name="scenario", value=scenario_name))
            result.parameters.extend(
                self._model["Parameter"](name=row["name"], value=row["value"]) for row in parameters
            )
            result.parameters.append(self._model["Parameter"](name="pickleId", value=pickle.id))

        with self._lifecycle.start_container(uuid=container_uuid) as container:
            container.name = f"Scenario fixtures: {name}"
            container.children.append(result_uuid)
            container.start = start
        self._active_cases[started.id] = case
        self._cases_by_attempt[started.id] = case
        result_uuids = self._case_result_uuids.setdefault(test_case.id, [])
        result_uuids.append(result_uuid)
        if self._first_result_uuid is None:
            self._first_result_uuid = result_uuid
            for attachment, fallback_label in self._pending_run_attachments:
                self._attach_to_result(attachment, result_uuid, fallback_label=fallback_label)
            self._pending_run_attachments.clear()
        for attachment in self._pending_case_attachments.get(test_case.id, []):
            self._attach_to_result(attachment, result_uuid)

    def _start_step(self, started: messages.TestStepStarted) -> None:
        case = self._active_cases.get(started.test_case_started_id)
        if case is None:
            raise AllureConversionError(
                f"test step start refers to unknown test case attempt {started.test_case_started_id!r}"
            )
        test_step = self._test_step(case, started.test_step_id)
        step_uuid = str(uuid4())
        timestamp = _timestamp_millis(started.timestamp)
        if test_step.pickle_step_id is not None:
            pickle_step = self._pickle_step(case, test_step.pickle_step_id)
            step_name = self._pickle_step_name(pickle_step)
            with self._lifecycle.start_step(parent_uuid=case.result_uuid, uuid=step_uuid) as allure_step:
                allure_step.name = step_name
                allure_step.start = timestamp
                self._add_step_arguments(allure_step, test_step, pickle_step)
            kind = "step"
            case.active_step_ids.append(started.test_step_id)
        else:
            hook = self._hooks.get(cast("str", test_step.hook_id))
            if hook is None:
                raise AllureConversionError(f"test step refers to unknown hook {test_step.hook_id!r}")
            hook_kind = _enum_value(hook.type)
            before = hook_kind.startswith("BEFORE_") or str(hook.name or "").lower().startswith("before")
            kind = "before" if before else "after"
            start_fixture = self._lifecycle.start_before_fixture if before else self._lifecycle.start_after_fixture
            with start_fixture(parent_uuid=case.container_uuid, uuid=step_uuid) as fixture:
                fixture.name = hook.name or ("Before" if before else "After")
                fixture.start = timestamp
                fixture.status = self._allure_status_value("unknown")
            case.active_step_ids.append(started.test_step_id)
        case.step_uuids[started.test_step_id] = _ActiveStep(step_uuid, kind)

    def _finish_step(self, finished: messages.TestStepFinished, wire: dict[str, Any]) -> None:
        case = self._active_cases.get(finished.test_case_started_id)
        if case is None:
            raise AllureConversionError(
                f"test step finish refers to unknown test case attempt {finished.test_case_started_id!r}"
            )
        step = case.step_uuids.get(finished.test_step_id)
        if step is None:
            raise AllureConversionError(f"test step finish refers to unknown step {finished.test_step_id!r}")
        status = _allure_status(_enum_value(finished.test_step_result.status))
        case.statuses.append(status)
        trace = self._step_trace(wire)
        details = _status_details(finished.test_step_result, trace)
        if status != "passed" and details:
            case.failures.append((status, details))
        update = (
            self._lifecycle.update_step
            if step.kind == "step"
            else (
                self._lifecycle.update_before_fixture if step.kind == "before" else self._lifecycle.update_after_fixture
            )
        )
        with update(step.uuid) as result:
            result.status = self._allure_status_value(status)
            result.stage = "finished"
            result.stop = _timestamp_millis(finished.timestamp)
            if details:
                result.statusDetails = self._model["StatusDetails"](**details)
        if step.kind == "step":
            self._lifecycle.stop_step(step.uuid)
        elif step.kind == "before":
            self._lifecycle.stop_before_fixture(step.uuid)
        else:
            self._lifecycle.stop_after_fixture(step.uuid)
        with suppress(ValueError):
            case.active_step_ids.remove(finished.test_step_id)

    def _finish_case(self, finished: messages.TestCaseFinished) -> None:
        case = self._active_cases.pop(finished.test_case_started_id, None)
        if case is None:
            raise AllureConversionError(
                f"test case finish refers to unknown test case attempt {finished.test_case_started_id!r}"
            )
        status = _scenario_status(tuple(case.statuses))
        with self._lifecycle.update_test_case(case.result_uuid) as result:
            result.status = self._allure_status_value(status)
            result.stage = "finished"
            result.stop = _timestamp_millis(finished.timestamp)
            if case.failures:
                _failure_status, details = max(case.failures, key=lambda item: _status_priority(item[0]))
                result.statusDetails = self._model["StatusDetails"](**details)
        result = self._lifecycle._get_item(uuid=case.result_uuid)
        if result is not None:
            self._write_result(result)
        container = self._lifecycle._pop_item(uuid=case.container_uuid)
        if container is not None:
            self._file_logger.report_container(container)
        self._session_children.append(case.result_uuid)

    def _start_run_hook(self, started: messages.TestRunHookStarted) -> None:
        hook = self._hooks.get(started.hook_id)
        if hook is None:
            raise AllureConversionError(f"test run hook start refers to unknown hook {started.hook_id!r}")
        container_uuid = self._ensure_session_container()
        before = _enum_value(hook.type) == "BEFORE_TEST_RUN"
        fixture_uuid = str(uuid4())
        start_fixture = self._lifecycle.start_before_fixture if before else self._lifecycle.start_after_fixture
        with start_fixture(parent_uuid=container_uuid, uuid=fixture_uuid) as fixture:
            fixture.name = hook.name or ("Before test run" if before else "After test run")
            fixture.start = _timestamp_millis(started.timestamp)
            fixture.status = self._allure_status_value("unknown")
        self._active_run_hooks[started.id] = _ActiveRunHook(fixture_uuid, "before" if before else "after")

    def _finish_run_hook(self, finished: messages.TestRunHookFinished, wire: dict[str, Any]) -> None:
        active = self._active_run_hooks.pop(finished.test_run_hook_started_id, None)
        if active is None:
            raise AllureConversionError(
                f"test run hook finish refers to unknown hook start {finished.test_run_hook_started_id!r}"
            )
        status = _allure_status(_enum_value(finished.result.status))
        details = _status_details(finished.result, self._hook_trace(wire))
        update = (
            self._lifecycle.update_before_fixture if active.kind == "before" else self._lifecycle.update_after_fixture
        )
        with update(active.fixture_uuid) as fixture:
            fixture.status = self._allure_status_value(status)
            fixture.stage = "finished"
            fixture.stop = _timestamp_millis(finished.timestamp)
            if details:
                fixture.statusDetails = self._model["StatusDetails"](**details)
        if active.kind == "before":
            self._lifecycle.stop_before_fixture(active.fixture_uuid)
        else:
            self._lifecycle.stop_after_fixture(active.fixture_uuid)

    def _attach(self, attachment: messages.Attachment) -> None:
        if attachment.media_type == _NATIVE_API_STEP_MEDIA_TYPE:
            self._attach_native_api_step(attachment)
            return
        if attachment.media_type == _NATIVE_API_ATTACHMENT_MEDIA_TYPE:
            self._attach_native_api_attachment(attachment)
            return

        parent_uuid: str | None = None
        case_id = attachment.test_case_started_id
        if case_id is None and attachment.test_run_hook_started_id is None:
            self._attach_unscoped(attachment)
            return
        if case_id is not None:
            case = self._active_cases.get(case_id)
            if case is None:
                raise AllureConversionError(
                    f"attachment {attachment.file_name or '<unnamed>'!r} refers to unknown scenario {case_id!r}"
                )
            if attachment.test_step_id is None:
                parent_uuid = case.result_uuid
            else:
                step = case.step_uuids.get(attachment.test_step_id)
                if step is None:
                    raise AllureConversionError(
                        f"attachment {attachment.file_name or '<unnamed>'!r} refers to unknown step "
                        f"{attachment.test_step_id!r}"
                    )
                parent_uuid = step.uuid
        elif attachment.test_run_hook_started_id is not None:
            run_hook = self._active_run_hooks.get(attachment.test_run_hook_started_id)
            if run_hook is None:
                raise AllureConversionError(
                    f"attachment {attachment.file_name or '<unnamed>'!r} refers to unknown test run hook "
                    f"{attachment.test_run_hook_started_id!r}"
                )
            parent_uuid = run_hook.fixture_uuid
        if parent_uuid is None:
            return

        self._attach_to_result(attachment, parent_uuid)

    def _attach_native_api_step(self, attachment: messages.Attachment) -> None:
        case = self._case_for_api_attachment(attachment)
        parent_uuid = self._api_parent_uuid(case, attachment.test_step_id)
        payload = self._decode_api_payload(attachment, expected_kind="step")
        self._materialize_api_step(payload, parent_uuid)

    def _attach_native_api_attachment(self, attachment: messages.Attachment) -> None:
        case = self._case_for_api_attachment(attachment)
        parent_uuid = self._api_parent_uuid(case, attachment.test_step_id)
        payload = self._decode_api_payload(attachment, expected_kind="attachment")
        self._materialize_api_attachment(payload, parent_uuid)

    def _case_for_api_attachment(self, attachment: messages.Attachment) -> _ActiveCase:
        attempt_id = attachment.test_case_started_id
        if attempt_id is None:
            raise AllureConversionError("native Allure API message has no test case attempt reference")
        case = self._cases_by_attempt.get(attempt_id)
        if case is None:
            raise AllureConversionError(f"native Allure API message refers to unknown attempt {attempt_id!r}")
        return case

    @staticmethod
    def _api_parent_uuid(case: _ActiveCase, test_step_id: str | None) -> str:
        if test_step_id is None:
            return case.result_uuid
        step = case.step_uuids.get(test_step_id)
        if step is None:
            raise AllureConversionError(f"native Allure API message refers to unknown step {test_step_id!r}")
        return step.uuid

    def _decode_api_payload(self, attachment: messages.Attachment, *, expected_kind: str) -> dict[str, Any]:
        try:
            raw_payload = _attachment_bytes(attachment)
            payload = json.loads(raw_payload)
        except (AllureConversionError, UnicodeDecodeError, ValueError, TypeError) as error:
            raise AllureConversionError("native Allure API message contains invalid JSON") from error
        if not isinstance(payload, dict) or payload.get("kind") != expected_kind:
            raise AllureConversionError(f"native Allure API message must contain a {expected_kind!r} payload")
        return payload

    def _materialize_api_step(self, payload: dict[str, Any], parent_uuid: str) -> None:
        name = payload.get("name")
        status = payload.get("status")
        start = payload.get("start")
        stop = payload.get("stop")
        parameters = payload.get("parameters", [])
        children = payload.get("steps", [])
        attachments = payload.get("attachments", [])
        details = payload.get("statusDetails")
        if not isinstance(name, str) or not name:
            raise AllureConversionError("native Allure API step has no name")
        if status not in {"passed", "failed", "broken", "skipped"}:
            raise AllureConversionError(f"native Allure API step has invalid status {status!r}")
        start = _api_timestamp(start, "start")
        stop = _api_timestamp(stop, "stop")
        if not isinstance(parameters, list) or not isinstance(children, list) or not isinstance(attachments, list):
            raise AllureConversionError("native Allure API step parameters, steps, and attachments must be arrays")
        if details is not None and not isinstance(details, dict):
            raise AllureConversionError("native Allure API step statusDetails must be an object or null")
        step_uuid = str(uuid4())
        with self._lifecycle.start_step(parent_uuid=parent_uuid, uuid=step_uuid) as step:
            step.name = name
            step.start = start
            step.stop = stop
            step.status = self._allure_status_value(status)
            step.stage = "finished"
            for parameter in parameters:
                if not isinstance(parameter, dict) or not isinstance(parameter.get("name"), str):
                    raise AllureConversionError("native Allure API step contains an invalid parameter")
                value = parameter.get("value")
                if not isinstance(value, str):
                    raise AllureConversionError("native Allure API step parameter values must be strings")
                step.parameters.append(self._model["Parameter"](name=parameter["name"], value=value))
            if details:
                normalized_details = {
                    key: value
                    for key, value in details.items()
                    if key in {"message", "trace"} and isinstance(value, str)
                }
                if normalized_details:
                    step.statusDetails = self._model["StatusDetails"](**normalized_details)
        for child in children:
            if not isinstance(child, dict):
                raise AllureConversionError("native Allure API nested steps must be objects")
            self._materialize_api_step(child, step_uuid)
        for api_attachment in attachments:
            if not isinstance(api_attachment, dict):
                raise AllureConversionError("native Allure API step attachments must be objects")
            self._materialize_api_attachment(api_attachment, step_uuid)
        self._lifecycle.stop_step(step_uuid)

    def _materialize_api_attachment(self, payload: dict[str, Any], parent_uuid: str) -> None:
        name = payload.get("name")
        media_type = payload.get("mediaType")
        extension = payload.get("extension")
        encoded_body = payload.get("body")
        size = payload.get("size")
        if not isinstance(name, str) or not isinstance(media_type, str) or not media_type:
            raise AllureConversionError("native Allure API attachment has an invalid name or media type")
        if not isinstance(extension, str):
            raise AllureConversionError("native Allure API attachment extension must be a string")
        if not isinstance(encoded_body, str):
            raise AllureConversionError("native Allure API attachment body must be base64 text")
        try:
            body = base64.b64decode(encoded_body, validate=True)
        except (binascii.Error, ValueError) as error:
            raise AllureConversionError("native Allure API attachment has malformed base64 content") from error
        if isinstance(size, bool) or not isinstance(size, int) or size != len(body):
            raise AllureConversionError("native Allure API attachment size does not match its content")
        extension = _safe_api_extension(extension)
        attachment_uuid = str(uuid4())
        file_name = self._lifecycle._attach(
            uuid=attachment_uuid,
            name=name,
            attachment_type=media_type,
            extension=extension,
            parent_uuid=parent_uuid,
        )
        self._file_logger.report_attached_data(body=body, file_name=file_name)

    def _attach_unscoped(self, attachment: messages.Attachment) -> None:
        case_id = _attachment_case_id(attachment)
        if case_id is not None and case_id in self._test_cases:
            self._pending_case_attachments.setdefault(case_id, []).append(attachment)
            for result_uuid in self._case_result_uuids.get(case_id, []):
                self._attach_to_result(attachment, result_uuid)
            return

        if case_id is None:
            fallback_label = "Cucumber run-level fallback"
        else:
            fallback_label = f"Cucumber unmapped testCaseId {case_id!r} fallback"
        if self._first_result_uuid is None:
            self._pending_run_attachments.append((attachment, fallback_label))
            return
        self._attach_to_result(attachment, self._first_result_uuid, fallback_label=fallback_label)

    def _attach_to_result(
        self,
        attachment: messages.Attachment,
        parent_uuid: str,
        *,
        fallback_label: str | None = None,
    ) -> None:
        attachment_uuid = str(uuid4())
        name = _safe_attachment_name(attachment.file_name, attachment_uuid)
        if fallback_label is not None:
            name = f"{fallback_label}: {name}"
        media_type = attachment.media_type
        extension = mimetypes.guess_extension(media_type.split(";", 1)[0]) or ".attach"
        try:
            body = _attachment_bytes(attachment)
        except AllureConversionError:
            raise
        file_name = self._lifecycle._attach(
            uuid=attachment_uuid,
            name=name,
            attachment_type=media_type,
            extension=extension.lstrip("."),
            parent_uuid=parent_uuid,
        )
        # Keep native attachments in this destination without broadcasting them globally.
        self._file_logger.report_attached_data(body=body, file_name=file_name)

    def _finish_session(self, finished: messages.TestRunFinished, wire: dict[str, Any]) -> None:
        if self._active_cases:
            active_ids = ", ".join(sorted(self._active_cases))
            raise AllureConversionError(f"test run finished with active scenario attempts: {active_ids}")
        if self._active_run_hooks:
            active_ids = ", ".join(sorted(self._active_run_hooks))
            raise AllureConversionError(f"test run finished with active run hooks: {active_ids}")
        if self._first_result_uuid is None and (self._pending_run_attachments or self._pending_case_attachments):
            raise AllureConversionError("cannot preserve unscoped Cucumber attachments without a completed scenario")
        if self._first_result_uuid is not None:
            for case_id, attachments in self._pending_case_attachments.items():
                if self._case_result_uuids.get(case_id):
                    continue
                fallback_label = f"Cucumber unmapped testCaseId {case_id!r} fallback"
                for attachment in attachments:
                    self._attach_to_result(attachment, self._first_result_uuid, fallback_label=fallback_label)
        # Keep completed results in the lifecycle until the run ends. Extension
        # attachments can arrive after TestCaseFinished and update the same file.
        for result_uuids in self._case_result_uuids.values():
            for result_uuid in result_uuids:
                result = self._lifecycle._get_item(uuid=result_uuid)
                if result is not None:
                    self._write_result(result)
        trace = self._run_trace(wire)
        container_uuid = self._ensure_session_container()
        with self._lifecycle.update_container(container_uuid) as container:
            container.children.extend(self._session_children)
            container.stop = _timestamp_millis(finished.timestamp)
            if finished.message or finished.exception is not None:
                detail = finished.message or getattr(finished.exception, "message", None) or "Test run failed"
                fixture = self._model["TestAfterResult"](
                    name="pytest test run",
                    status=self._allure_status_value("broken"),
                    stage="finished",
                    start=container.stop,
                    stop=container.stop,
                    statusDetails=self._model["StatusDetails"](
                        message=str(detail),
                        trace=trace or getattr(finished.exception, "stack_trace", None),
                    ),
                )
                container.afters.append(fixture)
        session_container = self._lifecycle._pop_item(uuid=container_uuid)
        if session_container is not None:
            self._file_logger.report_container(session_container)
            self._session_container_reported = True

    def _finish_partial_session(self) -> None:
        """Persist known session fixtures if pytest exits before TestRunFinished."""
        if self._session_container_reported:
            return
        if (
            self._session_container_uuid is None
            and not self._active_run_hooks
            and not self._session_children
            and not self._case_result_uuids
        ):
            return

        stopped_at = time.time_ns() // 1_000_000
        for active in self._active_run_hooks.values():
            update_fixture = (
                self._lifecycle.update_before_fixture
                if active.kind == "before"
                else self._lifecycle.update_after_fixture
            )
            with update_fixture(active.fixture_uuid) as fixture:
                fixture.status = self._allure_status_value("unknown")
                fixture.stage = "finished"
                fixture.stop = stopped_at
            if active.kind == "before":
                self._lifecycle.stop_before_fixture(active.fixture_uuid)
            else:
                self._lifecycle.stop_after_fixture(active.fixture_uuid)
        self._active_run_hooks.clear()

        active_result_uuids = {case.result_uuid for case in self._active_cases.values()}
        for result_uuids in self._case_result_uuids.values():
            for result_uuid in result_uuids:
                if result_uuid in active_result_uuids:
                    continue
                result = self._lifecycle._get_item(uuid=result_uuid)
                if result is not None:
                    self._write_result(result)

        container_uuid = self._ensure_session_container()
        with self._lifecycle.update_container(container_uuid) as container:
            container.children.extend(child for child in self._session_children if child not in container.children)
            container.stop = stopped_at
        session_container = self._lifecycle._pop_item(uuid=container_uuid)
        if session_container is not None:
            self._file_logger.report_container(session_container)
            self._session_container_reported = True

    def _write_result(self, result: Any) -> None:
        result_uuid = result.uuid
        destination = self.output_dir / f"{result_uuid}-result.json"
        temporary = self.output_dir / f".{result_uuid}-result.json.tmp"
        data = self._asdict(result, filter=lambda _key, value: value or value is False)
        indent = self._allure_indent if os.environ.get("ALLURE_INDENT_OUTPUT") else None
        try:
            with temporary.open("w", encoding="utf-8") as output:
                json.dump(data, output, indent=indent, ensure_ascii=False)
            os.replace(temporary, destination)
        except OSError as error:
            with suppress(OSError):
                temporary.unlink()
            raise AllureConversionError(f"cannot write native Allure result to {destination}: {error}") from error

    def _ensure_session_container(self) -> str:
        if self._session_container_uuid is None:
            self._session_container_uuid = str(uuid4())
            with self._lifecycle.start_container(uuid=self._session_container_uuid) as container:
                container.name = "Test session"
        return self._session_container_uuid

    def _test_step(self, case: _ActiveCase, test_step_id: str) -> messages.TestStep:
        for test_step in case.test_case.test_steps:
            if test_step.id == test_step_id:
                return test_step
        raise AllureConversionError(f"test case {case.test_case.id!r} has no test step {test_step_id!r}")

    def _pickle_step(self, case: _ActiveCase, pickle_step_id: str) -> messages.PickleStep:
        for pickle_step in case.pickle.steps:
            if pickle_step.id == pickle_step_id:
                return pickle_step
        raise AllureConversionError(f"pickle {case.pickle.id!r} has no step {pickle_step_id!r}")

    def _pickle_step_name(self, pickle_step: messages.PickleStep) -> str:
        keyword = ""
        for ast_node_id in pickle_step.ast_node_ids:
            source_step = self._registry.resolve(ast_node_id)
            source_keyword = getattr(source_step, "keyword", None)
            if isinstance(source_keyword, str) and source_keyword:
                keyword = source_keyword
                break
        return f"{keyword}{pickle_step.text}" if keyword else pickle_step.text

    def _add_step_arguments(
        self,
        allure_step: Any,
        test_step: messages.TestStep,
        pickle_step: messages.PickleStep,
    ) -> None:
        presentation = _pickle_step_argument_presentation(pickle_step)
        if presentation is not None:
            allure_step.description = presentation.get("description")
            allure_step.descriptionHtml = presentation.get("descriptionHtml")
            allure_step.parameters.extend(
                self._model["Parameter"](name=item["name"], value=item["value"])
                for item in presentation.get("parameters", [])
            )
        for match_list in test_step.step_match_arguments_lists or []:
            for index, argument in enumerate(match_list.step_match_arguments):
                group = argument.group
                if group.value is None:
                    continue
                name = argument.parameter_type_name or f"argument{index + 1}"
                allure_step.parameters.append(self._model["Parameter"](name=name, value=group.value))

    def _gherkin_identity(self, pickle: messages.Pickle) -> tuple[Any | None, Any | None, Any | None]:
        ast_node_ids = set(pickle.ast_node_ids)
        for envelope in self._registry.envelopes:
            document = envelope.gherkin_document
            if document is None or document.feature is None:
                continue
            feature = document.feature
            for child in feature.children:
                if child.scenario is not None and child.scenario.id in ast_node_ids:
                    return feature, None, child.scenario
                if child.rule is None:
                    continue
                for rule_child in child.rule.children:
                    if rule_child.scenario is not None and rule_child.scenario.id in ast_node_ids:
                        return feature, child.rule, rule_child.scenario
        return None, None, None

    def _step_trace(self, wire: dict[str, Any]) -> str | None:
        payload = wire.get("testStepFinished") or wire.get("test_step_finished")
        if not isinstance(payload, dict):
            return None
        result = payload.get("testStepResult") or payload.get("test_step_result")
        if not isinstance(result, dict):
            return None
        exception = result.get("exception")
        trace = exception.get("stackTrace") if isinstance(exception, dict) else None
        if not isinstance(trace, str):
            return None
        return trace

    @staticmethod
    def _hook_trace(wire: dict[str, Any]) -> str | None:
        payload = wire.get("testRunHookFinished") or wire.get("test_run_hook_finished")
        result = payload.get("result") if isinstance(payload, dict) else None
        exception = result.get("exception") if isinstance(result, dict) else None
        trace = exception.get("stackTrace") if isinstance(exception, dict) else None
        return trace if isinstance(trace, str) else None

    @staticmethod
    def _run_trace(wire: dict[str, Any]) -> str | None:
        payload = wire.get("testRunFinished") or wire.get("test_run_finished")
        exception = payload.get("exception") if isinstance(payload, dict) else None
        trace = exception.get("stackTrace") if isinstance(exception, dict) else None
        return trace if isinstance(trace, str) else None

    def _allure_status_value(self, status: str) -> Any:
        normalized = status.upper()
        return getattr(self._model["Status"], normalized, self._model["Status"].BROKEN)

    def _make_api_hooks(self) -> object:
        """Build lazily decorated hooks so allure-python-commons stays optional."""
        hookimpl = self._allure_commons.hookimpl
        reporter = self

        class AllureApiHooks:
            @hookimpl  # type: ignore[untyped-decorator]  # allure-python-commons does not type its Pluggy marker.
            def start_step(self, uuid: str, title: str, params: dict[str, Any] | None) -> None:
                reporter._start_api_step(uuid, title, params)

            @hookimpl  # type: ignore[untyped-decorator]
            def stop_step(
                self,
                uuid: str,
                exc_type: type[BaseException] | None,
                exc_val: BaseException | None,
                exc_tb: Any,
            ) -> None:
                reporter._finish_api_step(uuid, exc_type, exc_val, exc_tb)

            @hookimpl  # type: ignore[untyped-decorator]
            def attach_data(
                self,
                body: str | bytes,
                name: str,
                attachment_type: Any,
                extension: str | None,
            ) -> None:
                reporter._attach_api_data(body, name, attachment_type, extension)

            @hookimpl  # type: ignore[untyped-decorator]
            def attach_file(
                self,
                source: str,
                name: str,
                attachment_type: Any,
                extension: str | None,
            ) -> None:
                reporter._attach_api_file(source, name, attachment_type, extension)

        return AllureApiHooks()

    def _start_api_step(self, api_uuid: str, title: str, params: dict[str, Any] | None) -> None:
        case = next(reversed(self._active_cases.values()), None)
        if case is None:
            return
        step_params = params or {}
        parent_uuid = case.step_uuids[case.active_step_ids[-1]].uuid if case.active_step_ids else case.result_uuid
        step_uuid = f"api-{api_uuid}"
        with self._lifecycle.start_step(parent_uuid=parent_uuid, uuid=step_uuid) as step:
            step.name = title
            step.parameters.extend(
                self._model["Parameter"](name=name, value=str(value)) for name, value in step_params.items()
            )
        self._api_step_uuids[api_uuid] = step_uuid
        self._api_step_stack.append((api_uuid, step_uuid))

    def _finish_api_step(
        self,
        api_uuid: str,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        step_uuid = self._api_step_uuids.pop(api_uuid, None)
        if step_uuid is None:
            return
        self._api_step_stack = [entry for entry in self._api_step_stack if entry[0] != api_uuid]
        status = _allure_api_step_status(exc_type, exc_val)
        details: dict[str, str] = {}
        if exc_val is not None:
            details["message"] = str(exc_val)
            details["trace"] = "".join(traceback.format_exception(exc_type or type(exc_val), exc_val, exc_tb))
        with self._lifecycle.update_step(step_uuid) as step:
            step.status = self._allure_status_value(status)
            if details:
                step.statusDetails = self._model["StatusDetails"](**details)
        self._lifecycle.stop_step(step_uuid)

    def _attach_api_data(
        self,
        body: str | bytes,
        name: str,
        attachment_type: Any,
        extension: str | None,
    ) -> None:
        parent_uuid = self._active_api_parent()
        if parent_uuid is None:
            return
        media_type, resolved_extension = _api_attachment_properties(attachment_type, extension)
        file_name = self._lifecycle._attach(
            uuid=str(uuid4()),
            name=name,
            attachment_type=media_type,
            extension=resolved_extension,
            parent_uuid=parent_uuid,
        )
        self._file_logger.report_attached_data(body=body, file_name=file_name)

    def _attach_api_file(
        self,
        source: str,
        name: str,
        attachment_type: Any,
        extension: str | None,
    ) -> None:
        parent_uuid = self._active_api_parent()
        if parent_uuid is None:
            return
        media_type, resolved_extension = _api_attachment_properties(attachment_type, extension)
        file_name = self._lifecycle._attach(
            uuid=str(uuid4()),
            name=name,
            attachment_type=media_type,
            extension=resolved_extension,
            parent_uuid=parent_uuid,
        )
        self._file_logger.report_attached_file(source=source, file_name=file_name)

    def _active_api_parent(self) -> str | None:
        if self._api_step_stack:
            return self._api_step_stack[-1][1]
        case = next(reversed(self._active_cases.values()), None)
        if case is None:
            return None
        return case.step_uuids[case.active_step_ids[-1]].uuid if case.active_step_ids else case.result_uuid


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value)).upper()


def _api_timestamp(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AllureConversionError(f"native Allure API step {name} timestamp must be a non-negative integer")
    return value


def _api_attachment_properties(attachment_type: Any, extension: str | None) -> tuple[str | None, str]:
    media_type = getattr(attachment_type, "mime_type", attachment_type)
    if not isinstance(media_type, str):
        media_type = None
    resolved_extension = extension or getattr(attachment_type, "extension", None)
    if not isinstance(resolved_extension, str) or not resolved_extension:
        resolved_extension = mimetypes.guess_extension(media_type) if media_type is not None else None
    if not isinstance(resolved_extension, str) or not resolved_extension:
        resolved_extension = "attach"
    return media_type, _safe_api_extension(resolved_extension)


def _safe_api_extension(extension: str) -> str:
    normalized = extension[1:] if extension.startswith(".") else extension
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", normalized):
        raise AllureConversionError(f"unsafe Allure attachment extension: {extension!r}")
    return normalized


__all__ = ["NativeAllureDependencyError", "NativeAllureReporter"]
