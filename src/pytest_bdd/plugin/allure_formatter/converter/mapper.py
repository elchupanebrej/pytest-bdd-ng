"""Map Cucumber Messages events to Allure3 result objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from uuid import uuid4

import attrs

from .model import (
    AllureAttachment,
    AllureLabel,
    AllureParameter,
    AllureStatusDetails,
    AllureStepResult,
    AllureTestResult,
)

if TYPE_CHECKING:
    from pytest_bdd.model.execution_message_adapter import ExecutionProjection

    from .collector import StructuralContext


@attrs.define
class _MappingState:
    """Mutable state accumulated while mapping projections."""

    name: str = ""
    status: str = "passed"
    start_time: int = 0
    stop_time: int = 0
    description: str = ""
    status_details: AllureStatusDetails = attrs.Factory(AllureStatusDetails)
    steps: list[AllureStepResult] = attrs.Factory(list)
    attachments: list[AllureAttachment] = attrs.Factory(list)
    parameters: list[AllureParameter] = attrs.Factory(list)
    labels: list[AllureLabel] = attrs.Factory(list)
    step_id_to_index: dict[str, int] = attrs.Factory(dict)


def _resolve_step_name(
    test_step_id: str,
    structural: StructuralContext,
) -> str:
    """
    Resolve step name from TestStepStarted via lookup chain.

    Returns:
        The resolved step name, or empty string if not found.

    """
    for (kind, _id), payload in structural.items():
        if kind != "test_case":
            continue
        name = _find_step_name_from_test_case(test_step_id, payload, structural)
        if name:
            return name
    return ""


def _find_step_name_from_test_case(
    test_step_id: str,
    tc_payload: object,
    structural: StructuralContext,
) -> str:
    """
    Find step name by walking TestCase.test_steps -> Pickle.steps.

    Returns:
        The resolved step name, or empty string if not found.

    """
    test_steps = getattr(tc_payload, "test_steps", []) or []
    for ts in test_steps:
        if str(getattr(ts, "id", "")) != test_step_id:
            continue
        pickle_step_id = getattr(ts, "pickle_step_id", None)
        if pickle_step_id is None:
            continue
        pickle_id = getattr(tc_payload, "pickle_id", None)
        if pickle_id is None:
            continue
        return _find_pickle_step_text(str(pickle_step_id), str(pickle_id), structural)
    return ""


def _find_pickle_step_text(
    pickle_step_id: str,
    pickle_id: str,
    structural: StructuralContext,
) -> str:
    """
    Find PickleStep.text by pickle_step_id.

    Returns:
        The step text, or empty string if not found.

    """
    pickle_payload = structural.get(("pickle", pickle_id))
    if pickle_payload is None:
        return ""
    for ps in getattr(pickle_payload, "steps", []) or []:
        if str(getattr(ps, "id", "")) == pickle_step_id:
            return getattr(ps, "text", "") or ""
    return ""


def _find_pickle_for_test_case(
    test_case_id: str,
    structural: StructuralContext,
) -> object | None:
    """
    Find Pickle payload linked from a TestCase id.

    Returns:
        The linked Pickle payload, or None when unavailable.

    """
    tc = structural.get(("test_case", test_case_id))
    if tc is None:
        return None
    pickle_id = getattr(tc, "pickle_id", None)
    if pickle_id is None:
        return None
    return structural.get(("pickle", str(pickle_id)))


def _find_pickle_step_for_test_step(
    test_step_id: str,
    structural: StructuralContext,
) -> object | None:
    """
    Find PickleStep payload linked from a TestStep id.

    Returns:
        The linked PickleStep payload, or None when unavailable.

    """
    for (kind, _id), payload in structural.items():
        if kind != "test_case":
            continue
        for test_step in getattr(payload, "test_steps", []) or []:
            if str(getattr(test_step, "id", "")) != test_step_id:
                continue
            pickle_step_id = getattr(test_step, "pickle_step_id", None)
            pickle_id = getattr(payload, "pickle_id", None)
            if pickle_step_id is None or pickle_id is None:
                return None
            pickle_payload = structural.get(("pickle", str(pickle_id)))
            for pickle_step in getattr(pickle_payload, "steps", []) or []:
                if str(getattr(pickle_step, "id", "")) == str(pickle_step_id):
                    return cast("object", pickle_step)
    return None


def _resolve_test_case_name(
    test_case_id: str,
    structural: StructuralContext,
) -> str:
    """
    Resolve test case name from TestCaseStarted via lookup chain.

    Returns:
        The resolved test case name, or empty string if not found.

    """
    tc = structural.get(("test_case", str(test_case_id)))
    if tc is None:
        return ""
    pickle_id = getattr(tc, "pickle_id", None)
    if pickle_id is None:
        return ""
    pickle_payload = structural.get(("pickle", str(pickle_id)))
    if pickle_payload is None:
        return ""
    return getattr(pickle_payload, "name", "") or ""


def _resolve_hook_name(
    hook_id: str,
    structural: StructuralContext,
) -> str:
    """
    Resolve hook name from TestRunHookStarted via lookup chain.

    Returns:
        The resolved hook name, or empty string if not found.

    """
    hook = structural.get(("hook", str(hook_id)))
    if hook is None:
        return ""
    return getattr(hook, "name", None) or ""


def _handle_test_case_started(
    projection: ExecutionProjection,
    state: _MappingState,
    structural: StructuralContext,
) -> tuple[str, int]:
    """
    Handle TestCaseStarted event.

    Returns:
        Tuple of (name, start_time).

    """
    start_time = getattr(projection.payload, "timestamp", 0)
    test_case_id = getattr(projection.payload, "test_case_id", None)
    if test_case_id is None:
        test_case_id = getattr(projection.payload, "testCaseId", None)
    name = ""
    if test_case_id is not None:
        name = _resolve_test_case_name(str(test_case_id), structural)
        _add_pickle_id_parameter(str(test_case_id), structural, state.parameters)
        pickle_payload = _find_pickle_for_test_case(str(test_case_id), structural)
        if pickle_payload is not None:
            _add_tag_labels(pickle_payload, state.labels)
            state.description = _build_pickle_description(pickle_payload, structural)
    return name, start_time


def _add_tag_labels(pickle_payload: object, labels: list[AllureLabel]) -> None:
    """Add Pickle tags as Allure tag labels."""
    existing = {(label.name, label.value) for label in labels}
    for tag in getattr(pickle_payload, "tags", []) or []:
        tag_name = getattr(tag, "name", "") or ""
        if tag_name and ("tag", tag_name) not in existing:
            labels.append(AllureLabel(name="tag", value=str(tag_name)))
            existing.add(("tag", str(tag_name)))


def _build_pickle_description(pickle_payload: object, structural: StructuralContext) -> str:
    """
    Build Allure description from Gherkin Feature, Rule, and Scenario descriptions.

    Returns:
        Combined description text.

    """
    uri = getattr(pickle_payload, "uri", "") or ""
    document = structural.get(("gherkin_document", str(uri)))
    feature = getattr(document, "feature", None)
    if feature is None:
        return ""
    ast_node_ids = {str(item) for item in getattr(pickle_payload, "ast_node_ids", []) or []}
    descriptions: list[str] = []
    feature_description = _clean_description(getattr(feature, "description", ""))
    if feature_description:
        descriptions.append(feature_description)
    rule_description, scenario_description = _find_scenario_descriptions(feature, ast_node_ids)
    if rule_description:
        descriptions.append(rule_description)
    if scenario_description:
        descriptions.append(scenario_description)
    return "\n\n".join(descriptions)


def _find_scenario_descriptions(feature: object, ast_node_ids: set[str]) -> tuple[str, str]:
    """
    Find enclosing Rule and Scenario descriptions for pickle AST ids.

    Returns:
        Tuple of rule description and scenario description.

    """
    for child in getattr(feature, "children", []) or []:
        scenario = getattr(child, "scenario", None)
        if scenario is not None and str(getattr(scenario, "id", "")) in ast_node_ids:
            return "", _clean_description(getattr(scenario, "description", ""))
        rule = getattr(child, "rule", None)
        if rule is None:
            continue
        for rule_child in getattr(rule, "children", []) or []:
            scenario = getattr(rule_child, "scenario", None)
            if scenario is not None and str(getattr(scenario, "id", "")) in ast_node_ids:
                return (
                    _clean_description(getattr(rule, "description", "")),
                    _clean_description(getattr(scenario, "description", "")),
                )
    return "", ""


def _clean_description(description: object) -> str:
    """
    Normalize Gherkin description text.

    Returns:
        Stripped description.

    """
    return str(description or "").strip()


def _add_pickle_id_parameter(
    test_case_id: str,
    structural: StructuralContext,
    parameters: list[AllureParameter],
) -> None:
    """Add pickle ID as a parameter if available."""
    tc = structural.get(("test_case", test_case_id))
    if tc is None:
        return
    pickle_id = getattr(tc, "pickle_id", None)
    if pickle_id is not None:
        parameters.append(AllureParameter(name="pickleId", value=str(pickle_id)))


def _handle_test_step_finished(projection: ExecutionProjection, steps: list[AllureStepResult]) -> None:
    """Handle TestStepFinished event - update last step's status and stop time."""
    if steps:
        current_step = steps[-1]
        step_result = getattr(projection.payload, "test_step_result", None)
        finish_status = getattr(step_result, "status", "") if step_result else ""
        if hasattr(finish_status, "value"):
            finish_status = finish_status.value
        current_step.status = _map_status(str(finish_status))
        current_step.stop = getattr(projection.payload, "timestamp", 0)


def _handle_step_by_id(
    projection: ExecutionProjection,
    state: _MappingState,
    structural: StructuralContext,
) -> None:
    """Handle TestStepStarted/Finished events using step_id lookup."""
    test_step_id = getattr(projection.payload, "test_step_id", "") or ""
    event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))
    if event_type == "test_step_started":
        step_start = getattr(projection.payload, "timestamp", 0)
        step_name = _resolve_step_name(test_step_id, structural)
        pickle_step = _find_pickle_step_for_test_step(test_step_id, structural)
        idx = len(state.steps)
        state.steps.append(
            AllureStepResult(
                name=step_name,
                status="passed",
                start=step_start,
                description=_format_step_argument(pickle_step),
                descriptionHtml=_format_step_argument(pickle_step),
                parameters=_format_step_argument_parameters(pickle_step),
            ),
        )
        state.step_id_to_index[test_step_id] = idx
    elif event_type == "test_step_finished":
        step_idx = state.step_id_to_index.get(test_step_id)
        if step_idx is not None and step_idx < len(state.steps):
            _update_step_status(projection, state.steps[step_idx], state.status_details)


def _update_step_status(
    projection: ExecutionProjection,
    step: AllureStepResult,
    status_details: AllureStatusDetails,
) -> None:
    """Update a step's status and stop time from TestStepFinished."""
    step_result = getattr(projection.payload, "test_step_result", None)
    finish_status = getattr(step_result, "status", "") if step_result else ""
    if hasattr(finish_status, "value"):
        finish_status = finish_status.value
    step.status = _map_status(str(finish_status))
    step.stop = getattr(projection.payload, "timestamp", 0)
    message = getattr(step_result, "message", "") if step_result else ""
    exception = getattr(step_result, "exception", None) if step_result else None
    trace = getattr(exception, "stack_trace", "") or getattr(exception, "stackTrace", "") if exception else ""
    if step.status == "failed":
        step.statusDetails.message = str(message or getattr(exception, "message", "") or "")
        step.statusDetails.trace = str(trace or "")
        status_details.message = step.statusDetails.message
        status_details.trace = step.statusDetails.trace


def _format_step_argument(pickle_step: object | None) -> str:
    """
    Render PickleStep doc string or data table into an Allure step description.

    Returns:
        Step argument description text.

    """
    argument = getattr(pickle_step, "argument", None)
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
    """
    Render PickleStep argument as Allure parameters for UI consumption.

    Returns:
        Step parameters containing table or doc string payload.

    """
    argument = getattr(pickle_step, "argument", None)
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
    """
    Render a PickleTable as plain markdown for Allure.

    Returns:
        Markdown table text.

    """
    rows = []
    for row in getattr(data_table, "rows", []) or []:
        values = [str(getattr(cell, "value", "")) for cell in getattr(row, "cells", []) or []]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def _handle_run_level_event(
    projection: ExecutionProjection,
    steps: list[AllureStepResult],
    structural: StructuralContext,
) -> tuple[str, int, int, str, AllureStatusDetails]:
    """
    Handle run-level events (testRunStarted/Finished/Hook).

    Returns:
        Tuple of (name, start_time, stop_time, status, status_details).

    """
    event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))
    if event_type == "test_run_started":
        return "", getattr(projection.payload, "timestamp", 0), 0, "", AllureStatusDetails()
    if event_type == "test_run_finished":
        return _handle_test_run_finished(projection)
    if event_type == "test_run_hook_started":
        _handle_hook_started(projection, steps, structural)
        return "", 0, 0, "", AllureStatusDetails()
    if event_type == "test_run_hook_finished":
        _handle_hook_finished(projection, steps)
        return "", 0, 0, "", AllureStatusDetails()
    return "", 0, 0, "", AllureStatusDetails()


def _handle_test_run_finished(
    projection: ExecutionProjection,
) -> tuple[str, int, int, str, AllureStatusDetails]:
    """
    Handle testRunFinished event.

    Returns:
        Tuple of (name, start_time, stop_time, status, status_details).

    """
    stop_time = getattr(projection.payload, "timestamp", 0)
    success = getattr(projection.payload, "success", True)
    status = "failed" if not success else ""
    message = getattr(projection.payload, "message", "") or ""
    status_details = AllureStatusDetails()
    exception = getattr(projection.payload, "exception", None)
    if exception:
        exc_msg = getattr(exception, "message", "") or ""
        exc_trace = getattr(exception, "stackTrace", "") or getattr(exception, "stack_trace", "") or ""
        if not message:
            message = exc_msg
        status_details = AllureStatusDetails(message=message, trace=exc_trace)
    elif message:
        status_details = AllureStatusDetails(message=message)
    return "", 0, stop_time, status, status_details


def _handle_hook_started(
    projection: ExecutionProjection,
    steps: list[AllureStepResult],
    structural: StructuralContext,
) -> None:
    """Handle testRunHookStarted event."""
    hook_id = getattr(projection.payload, "hook_id", None)
    if hook_id is None:
        hook_id = getattr(projection.payload, "hookId", None)
    hook_name = _resolve_hook_name(str(hook_id), structural) if hook_id else ""
    if not hook_name:
        hook_name = f"hook:{hook_id}" if hook_id else "run-hook"
    hook_start = getattr(projection.payload, "timestamp", 0)
    steps.append(AllureStepResult(name=hook_name, status="passed", start=hook_start))


def _handle_hook_finished(projection: ExecutionProjection, steps: list[AllureStepResult]) -> None:
    """Handle testRunHookFinished event."""
    if not steps:
        return
    current_step = steps[-1]
    result = getattr(projection.payload, "result", None)
    if result:
        finish_status = getattr(result, "status", "") or ""
        if hasattr(finish_status, "value"):
            finish_status = finish_status.value
        current_step.status = _map_status(str(finish_status))
    hook_stop = getattr(projection.payload, "timestamp", 0)
    current_step.stop = hook_stop


def _handle_attachment(projection: ExecutionProjection, attachments: list[AllureAttachment]) -> None:
    """Handle attachment event."""
    att_name = getattr(projection.payload, "file_name", None)
    if not att_name:
        att_name = getattr(projection.payload, "media_type", None)
    if not att_name:
        att_name = "attachment"
    att_type = getattr(projection.payload, "media_type", None) or "text/plain"
    att_source = getattr(projection.payload, "source", "") or ""
    att_body = getattr(projection.payload, "body", None)
    att_encoding = getattr(projection.payload, "content_encoding", None)
    if att_encoding is not None and hasattr(att_encoding, "value"):
        att_encoding = att_encoding.value
    attachments.append(
        AllureAttachment(
            name=str(att_name),
            type=str(att_type),
            source=str(att_source),
            body=att_body,
            content_encoding=str(att_encoding) if att_encoding is not None else None,
        ),
    )


def _handle_test_case_finished_event(
    projection: ExecutionProjection,
    state: _MappingState,
    structural: StructuralContext,  # noqa: ARG001
) -> None:
    """Handle test_case_finished event."""
    state.stop_time = getattr(projection.payload, "timestamp", 0)
    if state.steps:
        state.status = state.steps[-1].status


def _handle_run_events(
    projection: ExecutionProjection,
    state: _MappingState,
    structural: StructuralContext,
) -> None:
    """Handle all test_run_* events."""
    run_level = _handle_run_level_event(projection, state.steps, structural)
    run_name, run_start, run_stop, run_status, run_details = run_level
    if run_name:
        state.name = run_name
    if run_start:
        state.start_time = run_start
    if run_stop:
        state.stop_time = run_stop
    if run_status:
        state.status = run_status
    if run_details.message:
        state.status_details = run_details


def _handle_fixture_event(projection: ExecutionProjection, state: _MappingState) -> None:
    """Handle fixture event."""
    fixture_name = getattr(projection.payload, "name", "")
    state.steps.append(AllureStepResult(name=fixture_name, status="passed"))


def _handle_unmapped_event(projection: ExecutionProjection, state: _MappingState) -> None:
    """Handle unmapped event types."""
    state.attachments.append(map_unmappable_to_attachment(projection))


def _dispatch_event(
    event_type: str,
    projection: ExecutionProjection,
    state: _MappingState,
    structural: StructuralContext,
) -> None:
    """
    Dispatch a single event to the appropriate handler, mutating state.

    Args:
        event_type: The cucumber message event type string.
        projection: The execution projection containing the event payload.
        state: Mutable mapping state being accumulated.
        structural: Structural context for lookup chains.

    """
    if event_type == "test_case_started":
        state.name, state.start_time = _handle_test_case_started(projection, state, structural)
    elif event_type == "test_case_finished":
        _handle_test_case_finished_event(projection, state, structural)
    elif event_type in {"test_step_started", "test_step_finished"}:
        _handle_step_by_id(projection, state, structural)
    elif event_type in {"test_run_started", "test_run_finished", "test_run_hook_started", "test_run_hook_finished"}:
        _handle_run_events(projection, state, structural)
    elif event_type == "attachment":
        _handle_attachment(projection, state.attachments)
    elif event_type == "fixture":
        _handle_fixture_event(projection, state)
    else:
        _handle_unmapped_event(projection, state)


def map_test_case_to_result(
    case_id: str,
    projections: list[ExecutionProjection],
    structural: StructuralContext | None = None,
) -> AllureTestResult:
    """
    Map a test case's cucumber message projections to an Allure TestResult.

    Returns:
        AllureTestResult with all mapped fields.

    """
    if structural is None:
        structural = {}

    state = _MappingState()

    for projection in projections:
        event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))
        _dispatch_event(event_type, projection, state, structural)

    _finalize_run_level(case_id, state.steps, state.attachments, state.status_details)

    result_uuid = str(uuid4()) if case_id.startswith("run:") else case_id

    return AllureTestResult(
        uuid=result_uuid,
        name=_get_final_name(case_id, state.name),
        status=state.status,
        statusDetails=state.status_details,
        labels=state.labels,
        links=[],
        steps=state.steps,
        attachments=state.attachments,
        parameters=state.parameters,
        description=state.description,
        descriptionHtml=state.description,
        start=state.start_time,
        stop=state.stop_time,
    )


def _get_final_name(case_id: str, name: str) -> str:
    """
    Get final result name, generating one for run-level events.

    Returns:
        The final result name.

    """
    if case_id.startswith("run:") and not name:
        return f"Test Run {case_id[4:]}"
    return name


def _finalize_run_level(
    case_id: str,
    steps: list[AllureStepResult],
    attachments: list[AllureAttachment],
    status_details: AllureStatusDetails,
) -> None:
    """Finalize result fields for run-level events."""
    if case_id.startswith("run:") and not steps and not attachments:
        status_details.message = status_details.message or "Run-level events only (no test cases executed)"


def _map_status(cucumber_status: str) -> str:
    """
    Map Cucumber status string to Allure status string.

    Returns:
        Allure-compatible status string.

    """
    status_map: dict[str, str] = {
        "passed": "passed",
        "failed": "failed",
        "skipped": "skipped",
        "pending": "skipped",
        "undefined": "skipped",
        "ambiguous": "failed",
        "unknown": "skipped",
    }
    return status_map.get(cucumber_status.lower(), "skipped")


def map_unmappable_to_attachment(
    projection: ExecutionProjection,
) -> AllureAttachment:
    """
    Encode unmappable events as structured metadata attachments.

    Returns:
        AllureAttachment with unmapped event data.

    """
    event_type = str(projection.payload_kind)
    return AllureAttachment(
        name=f"unmapped-{event_type}",
        type="application/json",
        source="",
    )
