"""CucumberEnvelopeAdapter — state machine for envelope routing."""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from attrs import define, field

from pytest_bdd.plugin.allure_formatter.converter.model import AllureParameter

if TYPE_CHECKING:
    from collections.abc import Callable

    from allure_commons.lifecycle import AllureLifecycle

    from pytest_bdd.model.execution_message_adapter import ExecutionProjection

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
    "undefined": "broken",
    "pending": "broken",
    "ambiguous": "broken",
}


def _map_status(raw: str) -> str:
    return _STATUS_MAP.get(str(raw).lower(), "broken")


_LARGE_TIMESTAMP_THRESHOLD = 1e11


def _to_ms(timestamp: object) -> int | None:  # noqa: PLR0911  # comprehensive timestamp conversion
    if timestamp is None:
        return None
    if hasattr(timestamp, "seconds") and hasattr(timestamp, "nanos"):
        return int(timestamp.seconds * 1000 + timestamp.nanos / 1_000_000)
    if isinstance(timestamp, dict):
        return int(timestamp.get("seconds", 0) * 1000 + timestamp.get("nanos", 0) / 1_000_000)
    if isinstance(timestamp, (int, float)):
        if timestamp == 0:
            return 0
        if timestamp > _LARGE_TIMESTAMP_THRESHOLD:
            return int(timestamp)
        return int(timestamp * 1000)
    return None


def _format_step_argument(pickle_step: object | None) -> str:
    argument = getattr(pickle_step, "argument", None) if pickle_step is not None else None
    if argument is None:
        return ""
    data_table = getattr(argument, "data_table", None)
    if data_table is not None:
        return _format_pickle_table(data_table)
    doc_string = getattr(argument, "doc_string", None)
    if doc_string is not None:
        content = getattr(doc_string, "content", "") or ""
        media_type = getattr(doc_string, "media_type", "") or ""
        if media_type:
            return f"{media_type}\n\n{content}"
        return str(content)
    return ""


def _format_step_argument_parameters(pickle_step: object | None) -> list[AllureParameter]:
    argument = getattr(pickle_step, "argument", None) if pickle_step is not None else None
    if argument is None:
        return []
    data_table = getattr(argument, "data_table", None)
    if data_table is not None:
        return [AllureParameter(name="dataTable", value=_format_pickle_table(data_table))]
    doc_string = getattr(argument, "doc_string", None)
    if doc_string is not None:
        return [AllureParameter(name="docString", value=str(getattr(doc_string, "content", "") or ""))]
    return []


def _format_pickle_table(data_table: object) -> str:
    rows = []
    for row in getattr(data_table, "rows", []) or []:
        values = [str(getattr(cell, "value", "")) for cell in getattr(row, "cells", []) or []]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


@define(eq=False, hash=False)
class EnvelopeStateCache:
    """
    Track test_case_started_id → Allure uuid mappings.

    Inspired by allure-pytest's ItemCache pattern (listener.py:283).
    """

    _case_uuids: dict[str, str] = field(factory=dict)
    _step_uuids: dict[str, str] = field(factory=dict)
    _case_statuses: dict[str, str] = field(factory=dict)
    _case_failures: dict[str, tuple[str, str]] = field(factory=dict)

    def get_case_uuid(self, case_started_id: str) -> str | None:
        return self._case_uuids.get(case_started_id)

    def set_case_uuid(self, case_started_id: str, uuid: str) -> None:
        self._case_uuids[case_started_id] = uuid

    def get_step_uuid(self, step_started_id: str) -> str | None:
        return self._step_uuids.get(step_started_id)

    def set_step_uuid(self, step_started_id: str, uuid: str) -> None:
        self._step_uuids[step_started_id] = uuid

    def get_case_status(self, case_started_id: str) -> str:
        return self._case_statuses.get(case_started_id, "passed")

    def update_case_status(self, case_started_id: str, status: str) -> None:
        current = self._case_statuses.get(case_started_id, "passed")
        rankings = {"failed": 4, "broken": 3, "skipped": 2, "passed": 1}
        if rankings.get(status, 0) > rankings.get(current, 0):
            self._case_statuses[case_started_id] = status

    def set_case_failure(self, case_started_id: str, message: str, trace: str) -> None:
        self._case_failures[case_started_id] = (message, trace)

    def get_case_failure(self, case_started_id: str) -> tuple[str, str] | None:
        return self._case_failures.get(case_started_id)

    def clear(self) -> None:
        self._case_uuids.clear()
        self._step_uuids.clear()
        self._case_statuses.clear()
        self._case_failures.clear()


@define(eq=False, hash=False)
class CucumberEnvelopeAdapter:
    """State machine routing envelopes by payload_kind to AllureLifecycle."""

    lifecycle: AllureLifecycle = field()
    state_cache: EnvelopeStateCache = field(factory=EnvelopeStateCache)
    session_container_children: list[str] | None = field(default=None)

    def route_envelope(self, projection: ExecutionProjection) -> None:
        try:
            cast(
                "Callable",
                {
                    "test_case_started": self._handle_test_case_started,
                    "test_step_started": self._handle_test_step_started,
                    "test_step_finished": self._handle_test_step_finished,
                    "test_case_finished": self._handle_test_case_finished,
                    "test_run_started": self._handle_test_run_started,
                    "test_run_finished": self._handle_test_run_finished,
                }[projection.payload_kind],
            )(projection)
        except KeyError:
            logger.debug("Unmapped payload_kind: %s", projection.payload_kind)

    def _handle_test_case_started(self, projection: ExecutionProjection) -> None:
        case_uuid = str(uuid4())
        self.state_cache.set_case_uuid(projection.payload_id or "", case_uuid)
        start = _to_ms(getattr(projection.payload, "timestamp", None))

        with self.lifecycle.schedule_test_case(case_uuid) as test_result:
            test_result.name = self._resolve_case_name(projection)
            test_result.start = start
            self._add_labels(projection, test_result)
            self._add_description(projection, test_result)
            self._add_parameters(projection, test_result)

        if self.session_container_children is not None:
            self.session_container_children.append(case_uuid)

    def _handle_test_step_started(self, projection: ExecutionProjection) -> None:
        case_started_id = getattr(projection.payload, "test_case_started_id", None) or ""
        case_uuid = self.state_cache.get_case_uuid(str(case_started_id))
        if case_uuid is None:
            logger.debug("No case uuid for test_case_started_id=%s", case_started_id)
            return

        step_uuid = str(uuid4())
        test_step_id = getattr(projection.payload, "test_step_id", None) or ""
        self.state_cache.set_step_uuid(str(test_step_id), step_uuid)
        start = _to_ms(getattr(projection.payload, "timestamp", None))

        step_name = self._resolve_step_name(projection)
        pickle_step = self._resolve_pickle_step(projection)
        description = _format_step_argument(pickle_step)
        parameters = _format_step_argument_parameters(pickle_step)
        with self.lifecycle.start_step(parent_uuid=case_uuid, uuid=step_uuid) as step:
            step.name = step_name
            step.start = start
            if description:
                step.description = description
                step.descriptionHtml = description
            if parameters:
                step.parameters = parameters

    def _handle_test_step_finished(self, projection: ExecutionProjection) -> None:
        test_step_id = getattr(projection.payload, "test_step_id", None) or ""
        step_uuid = self.state_cache.get_step_uuid(str(test_step_id))
        if step_uuid is None:
            logger.debug("No step uuid for test_step_id=%s", test_step_id)
            return

        stop = _to_ms(getattr(projection.payload, "timestamp", None))
        step_result_payload = getattr(projection.payload, "test_step_result", None)
        raw_status = ""
        if step_result_payload is not None:
            raw_status = getattr(step_result_payload, "status", "")
            if hasattr(raw_status, "value"):
                raw_status = raw_status.value

        status = _map_status(str(raw_status))
        with self.lifecycle.update_step(step_uuid) as step:
            step.status = status
            step.stop = stop

        self.lifecycle.stop_step(step_uuid)

        case_started_id = getattr(projection.payload, "test_case_started_id", None) or ""
        if case_started_id:
            self.state_cache.update_case_status(str(case_started_id), status)
            if status in {"failed", "broken"}:
                message = getattr(step_result_payload, "message", "") or ""
                exception = getattr(step_result_payload, "exception", None)
                trace = (
                    getattr(exception, "stack_trace", "") or getattr(exception, "stackTrace", "") if exception else ""
                )
                if not message and exception:
                    message = getattr(exception, "message", "") or ""
                self.state_cache.set_case_failure(str(case_started_id), str(message), str(trace))

    def _handle_test_case_finished(self, projection: ExecutionProjection) -> None:
        case_started_id = getattr(projection.payload, "test_case_started_id", None) or ""
        case_uuid = self.state_cache.get_case_uuid(str(case_started_id))
        if case_uuid is None:
            logger.debug("No case uuid for test_case_started_id=%s", case_started_id)
            return

        stop = _to_ms(getattr(projection.payload, "timestamp", None))
        case_result_payload = getattr(projection.payload, "test_case_result", None)
        raw_status = ""
        if case_result_payload is not None:
            raw_status = getattr(case_result_payload, "status", "")
            if hasattr(raw_status, "value"):
                raw_status = raw_status.value

        status = self.state_cache.get_case_status(str(case_started_id))
        if raw_status:
            mapped_raw = _map_status(str(raw_status))
            rankings = {"failed": 4, "broken": 3, "skipped": 2, "passed": 1}
            if rankings.get(mapped_raw, 0) > rankings.get(status, 0):
                status = mapped_raw

        with self.lifecycle.update_test_case(case_uuid) as test_result:
            test_result.status = status
            test_result.stop = stop
            if status in {"failed", "broken"}:
                failure = self.state_cache.get_case_failure(str(case_started_id))
                if failure:
                    from allure_commons.model2 import StatusDetails

                    msg, trc = failure
                    test_result.statusDetails = StatusDetails(message=str(msg), trace=str(trc))
                else:
                    self._set_failure_details(projection, test_result)

        self.lifecycle.write_test_case(case_uuid)

    def _handle_attachment(self, projection: ExecutionProjection) -> None:
        case_started_id = getattr(projection.payload, "test_case_started_id", None) or ""
        case_uuid = self.state_cache.get_case_uuid(str(case_started_id))
        if case_uuid is None:
            return

        att = projection.payload
        att_body = getattr(att, "body", None)
        att_source = getattr(att, "source", None)
        att_name = getattr(att, "name", "attachment") or "attachment"
        att_type = getattr(att, "media", None)
        if att_type is None:
            att_type = getattr(att, "attachment_type", None)
        att_encoding = getattr(att, "content_encoding", None) or ""

        ext_map = {
            "text/plain": "txt",
            "text/html": "html",
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/gif": "gif",
            "application/json": "json",
            "application/xml": "xml",
            "video/mp4": "mp4",
        }
        ext = ext_map.get(str(att_type).lower(), "attach") if att_type else "attach"

        attachment_uuid = str(uuid4())
        if att_body is not None:
            body_str = att_body if isinstance(att_body, str) else str(att_body)
            if str(att_encoding).upper() == "BASE64":
                try:
                    body_bytes = base64.b64decode(body_str)
                    self.lifecycle.attach_data(
                        uuid=attachment_uuid,
                        body=body_bytes,
                        name=att_name,
                        attachment_type=att_type,
                        extension=ext,
                        parent_uuid=case_uuid,
                    )
                except Exception:
                    self.lifecycle.attach_data(
                        uuid=attachment_uuid,
                        body=body_str,
                        name=att_name,
                        attachment_type=att_type,
                        extension=ext,
                        parent_uuid=case_uuid,
                    )
            else:
                self.lifecycle.attach_data(
                    uuid=attachment_uuid,
                    body=body_str,
                    name=att_name,
                    attachment_type=att_type,
                    extension=ext,
                    parent_uuid=case_uuid,
                )
        elif att_source:
            self.lifecycle.attach_file(
                uuid=attachment_uuid,
                source=att_source,
                name=att_name,
                attachment_type=att_type,
                extension=ext,
                parent_uuid=case_uuid,
            )

    def _handle_test_run_started(self, _projection: ExecutionProjection) -> None:
        self.state_cache.clear()

    def _handle_test_run_finished(self, projection: ExecutionProjection) -> None:
        pass

    def _resolve_case_name(self, projection: ExecutionProjection) -> str:  # noqa: PLR0911, PLR6301  # name resolution via registry
        test_case_id = getattr(projection.payload, "test_case_id", None)
        if test_case_id is None:
            return ""
        registry = projection.registry
        if registry is None:
            return ""
        try:
            tc = registry.resolve_typed("TestCase", str(test_case_id))
        except KeyError:
            return ""
        if tc is None:
            return ""
        pickle_id = getattr(tc, "pickle_id", None)
        if pickle_id is None:
            return ""
        try:
            pickle_payload = registry.resolve_typed("Pickle", str(pickle_id))
        except KeyError:
            return ""
        if pickle_payload is None:
            return ""
        return getattr(pickle_payload, "name", "") or ""

    def _resolve_step_name(self, projection: ExecutionProjection) -> str:  # noqa: C901, PLR0911, PLR0912, PLR6301  # step naming logic
        test_step_id = getattr(projection.payload, "test_step_id", None)
        if test_step_id is None:
            return ""
        registry = projection.registry
        if registry is None:
            return ""
        test_case_id = getattr(projection.payload, "test_case_id", None)
        if test_case_id is None:
            case_started_id = getattr(projection.payload, "test_case_started_id", None)
            if case_started_id is not None:
                try:
                    tc_started = registry.resolve_typed("TestCaseStarted", str(case_started_id))
                    test_case_id = getattr(tc_started, "test_case_id", None)
                except (KeyError, Exception):
                    pass
        if test_case_id is None:
            return ""
        try:
            tc = registry.resolve_typed("TestCase", str(test_case_id))
        except KeyError:
            return ""
        if tc is None:
            return ""
        test_steps = getattr(tc, "test_steps", []) or []
        for ts in test_steps:
            ts_id = getattr(ts, "id", "")
            if str(ts_id) != str(test_step_id):
                continue
            pickle_step_id = getattr(ts, "pickle_step_id", None)
            if pickle_step_id is None:
                continue
            try:
                pickle_step = registry.resolve_typed("PickleStep", str(pickle_step_id))
            except KeyError:
                continue
            if pickle_step is None:
                continue
            return getattr(pickle_step, "text", "") or getattr(pickle_step, "name", "") or ""
        return ""

    def _resolve_pickle_step(self, projection: ExecutionProjection) -> object | None:  # noqa: C901, PLR0911, PLR6301  # step resolution
        test_step_id = getattr(projection.payload, "test_step_id", None)
        if test_step_id is None:
            return None
        registry = projection.registry
        if registry is None:
            return None
        test_case_id = getattr(projection.payload, "test_case_id", None)
        if test_case_id is None:
            case_started_id = getattr(projection.payload, "test_case_started_id", None)
            if case_started_id is not None:
                try:
                    tc_started = registry.resolve_typed("TestCaseStarted", str(case_started_id))
                    test_case_id = getattr(tc_started, "test_case_id", None)
                except (KeyError, Exception):
                    pass
        if test_case_id is None:
            return None
        try:
            tc = registry.resolve_typed("TestCase", str(test_case_id))
        except KeyError:
            return None
        if tc is None:
            return None
        test_steps = getattr(tc, "test_steps", []) or []
        for ts in test_steps:
            ts_id = getattr(ts, "id", "")
            if str(ts_id) != str(test_step_id):
                continue
            pickle_step_id = getattr(ts, "pickle_step_id", None)
            if pickle_step_id is None:
                continue
            try:
                return registry.resolve_typed("PickleStep", str(pickle_step_id))
            except KeyError:
                continue
        return None

    def _add_labels(self, projection: ExecutionProjection, test_result: Any) -> None:  # noqa: PLR6301  # method for context access
        test_case_id = getattr(projection.payload, "test_case_id", None)
        if test_case_id is None:
            return
        registry = projection.registry
        if registry is None:
            return
        try:
            tc = registry.resolve_typed("TestCase", str(test_case_id))
        except KeyError:
            return
        if tc is None:
            return
        pickle_id = getattr(tc, "pickle_id", None)
        if pickle_id is None:
            return
        try:
            pickle_payload = registry.resolve_typed("Pickle", str(pickle_id))
        except KeyError:
            return
        existing = set()
        for tag in getattr(pickle_payload, "tags", []) or []:
            tag_name = getattr(tag, "name", "") or ""
            if tag_name and ("tag", tag_name) not in existing:
                from allure_commons.model2 import Label

                test_result.labels.append(Label(name="tag", value=str(tag_name)))
                existing.add(("tag", str(tag_name)))

    def _add_description(self, projection: ExecutionProjection, test_result: Any) -> None:  # noqa: C901, PLR0911, PLR0912, PLR6301  # description extraction
        test_case_id = getattr(projection.payload, "test_case_id", None)
        if test_case_id is None:
            return
        registry = projection.registry
        if registry is None:
            return
        try:
            tc = registry.resolve_typed("TestCase", str(test_case_id))
        except KeyError:
            return
        if tc is None:
            return
        pickle_id = getattr(tc, "pickle_id", None)
        if pickle_id is None:
            return
        try:
            pickle_payload = registry.resolve_typed("Pickle", str(pickle_id))
        except KeyError:
            return
        uri = getattr(pickle_payload, "uri", "") or ""
        ast_node_ids = {str(item) for item in getattr(pickle_payload, "ast_node_ids", []) or []}
        try:
            doc = cast("dict", registry.objects_by_id).get(("gherkin_document", uri))
        except Exception:
            doc = None
        if doc is None:
            return
        feature = getattr(doc, "feature", None)
        if feature is None:
            return
        descriptions: list[str] = []
        feature_desc = str(getattr(feature, "description", "") or "").strip()
        if feature_desc:
            descriptions.append(feature_desc)
        for child in getattr(feature, "children", []) or []:
            scenario = getattr(child, "scenario", None)
            if scenario is not None and str(getattr(scenario, "id", "")) in ast_node_ids:
                desc = str(getattr(scenario, "description", "") or "").strip()
                if desc:
                    descriptions.append(desc)
                break
            rule = getattr(child, "rule", None)
            if rule is None:
                continue
            for rule_child in getattr(rule, "children", []) or []:
                scenario = getattr(rule_child, "scenario", None)
                if scenario is not None and str(getattr(scenario, "id", "")) in ast_node_ids:
                    rule_desc = str(getattr(rule, "description", "") or "").strip()
                    if rule_desc:
                        descriptions.append(rule_desc)
                    desc = str(getattr(scenario, "description", "") or "").strip()
                    if desc:
                        descriptions.append(desc)
                    break
        test_result.description = "\n\n".join(descriptions)

    def _add_parameters(self, projection: ExecutionProjection, test_result: Any) -> None:  # noqa: PLR6301  # method for context access
        test_case_id = getattr(projection.payload, "test_case_id", None)
        if test_case_id is None:
            return
        registry = projection.registry
        if registry is None:
            return
        try:
            tc = registry.resolve_typed("TestCase", str(test_case_id))
        except KeyError:
            return
        pickle_id = getattr(tc, "pickle_id", None)
        if pickle_id is not None:
            from allure_commons.model2 import Parameter

            test_result.parameters.append(Parameter(name="pickleId", value=str(pickle_id)))

    def _set_failure_details(self, projection: ExecutionProjection, test_result: Any) -> None:  # noqa: PLR6301  # method for context access
        case_result_payload = getattr(projection.payload, "test_case_result", None)
        if case_result_payload is None:
            return
        message = getattr(case_result_payload, "message", "") or ""
        exception = getattr(case_result_payload, "exception", None)
        trace = ""
        if exception is not None:
            trace = getattr(exception, "stack_trace", "") or getattr(exception, "stackTrace", "") or ""
            if not message:
                message = getattr(exception, "message", "") or ""
        from allure_commons.model2 import StatusDetails

        test_result.statusDetails = StatusDetails(message=str(message), trace=str(trace))
