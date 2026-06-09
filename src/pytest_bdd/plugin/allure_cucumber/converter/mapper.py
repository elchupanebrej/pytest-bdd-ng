"""Map Cucumber Messages events to Allure3 result objects."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

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


def _resolve_step_name(
    test_step_id: str,
    structural: StructuralContext,
) -> str:
    """
    Resolve step name from TestStepStarted via lookup chain.

    Chain: TestStepStarted.test_step_id
      → TestCase.test_steps[] where TestStep.id == test_step_id
        → TestStep.pickle_step_id / Hook.id
          → Pickle.steps[] where PickleStep.id == pickle_step_id
            → PickleStep.text
    """
    for (kind, _id), payload in structural.items():
        if kind == "test_case":
            test_steps = getattr(payload, "test_steps", []) or []
            for ts in test_steps:
                if str(getattr(ts, "id", "")) == test_step_id:
                    pickle_step_id = getattr(ts, "pickle_step_id", None)
                    if pickle_step_id is not None:
                        pickle_id = getattr(payload, "pickle_id", None)
                        if pickle_id is not None:
                            pickle_payload = structural.get(("pickle", str(pickle_id)))
                            if pickle_payload is not None:
                                steps = getattr(pickle_payload, "steps", []) or []
                                for ps in steps:
                                    if str(getattr(ps, "id", "")) == str(pickle_step_id):
                                        return getattr(ps, "text", "") or ""

                    # Resolve hook step name
                    hook_id = getattr(ts, "hook_id", None)
                    if hook_id is None:
                        hook_id = getattr(ts, "hookId", None)
                    if hook_id is not None:
                        hook_name = _resolve_hook_name(str(hook_id), structural)
                        if hook_name:
                            return hook_name
                        return f"hook:{hook_id}"
    return ""


def _resolve_test_case_name(
    test_case_id: str,
    structural: StructuralContext,
) -> str:
    """
    Resolve test case name from TestCaseStarted via lookup chain.

    Chain: TestCaseStarted.test_case_id
      → TestCase[] where TestCase.id == test_case_id
        → TestCase.pickle_id
          → Pickle[] where Pickle.id == pickle_id
            → Pickle.name
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

    Chain: TestRunHookStarted.hook_id
      → Hook[] where Hook.id == hook_id
        → Hook.name
    """
    hook = structural.get(("hook", str(hook_id)))
    if hook is None:
        return ""
    return getattr(hook, "name", None) or ""


def _handle_test_case_started(
    projection: ExecutionProjection,
    parameters: list[AllureParameter],
    structural: StructuralContext,
) -> tuple[str, int]:
    """
    Handle TestCaseStarted event.

    Returns:
        Tuple of (name, start_time).

    """
    start_time = getattr(projection.payload, "timestamp", 0)

    # Resolve name from Pickle via TestCase lookup chain
    test_case_id = getattr(projection.payload, "test_case_id", None)
    if test_case_id is None:
        test_case_id = getattr(projection.payload, "testCaseId", None)
    name = ""
    if test_case_id is not None:
        name = _resolve_test_case_name(str(test_case_id), structural)

    # Resolve pickle_id parameter
    if test_case_id is not None:
        tc = structural.get(("test_case", str(test_case_id)))
        if tc is not None:
            pickle_id = getattr(tc, "pickle_id", None)
            if pickle_id is not None:
                parameters.append(AllureParameter(name="pickleId", value=str(pickle_id)))

    return name, start_time


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


def map_test_case_to_result(
    case_id: str,
    projections: list[ExecutionProjection],
    structural: StructuralContext | None = None,
) -> AllureTestResult:
    """
    Map a test case's cucumber message projections to an Allure TestResult.

    Mapping table:
    - TestCaseStarted → AllureTestResult (name, labels, start time)
    - TestStepStarted → AllureStepResult (name via lookup chain, start time)
    - TestStepFinished → AllureStepResult (status, stop time)
    - Attachment → AllureAttachment (file_name→name, source, media_type→type)
    - testRunStarted → sets start time
    - testRunFinished → sets stop time, status from success field
    - testRunHookStarted → AllureStepResult for the hook (name via Hook lookup)
    - testRunHookFinished → updates hook step status
    - Unmappable events → structured attachments (never dropped)

    Returns:
        AllureTestResult with all mapped fields.

    """
    if structural is None:
        structural = {}

    labels: list[AllureLabel] = []
    steps: list[AllureStepResult] = []
    attachments: list[AllureAttachment] = []
    parameters: list[AllureParameter] = []
    name = ""
    status = "passed"
    start_time = 0
    stop_time = 0
    status_details = AllureStatusDetails()

    # Track step IDs to resolve names from TestStepStarted
    step_id_to_index: dict[str, int] = {}

    for projection in projections:
        event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))

        if event_type == "test_case_started":
            name, start_time = _handle_test_case_started(projection, parameters, structural)
        elif event_type == "test_case_finished":
            stop_time = getattr(projection.payload, "timestamp", 0)
            if steps:
                status = steps[-1].status
        elif event_type == "test_step_started":
            test_step_id = getattr(projection.payload, "test_step_id", "") or ""
            step_start = getattr(projection.payload, "timestamp", 0)
            step_name = _resolve_step_name(test_step_id, structural)
            idx = len(steps)
            steps.append(AllureStepResult(name=step_name, status="passed", start=step_start))
            step_id_to_index[test_step_id] = idx
        elif event_type == "test_step_finished":
            test_step_id = getattr(projection.payload, "test_step_id", "") or ""
            idx = step_id_to_index.get(test_step_id)
            if idx is not None and idx < len(steps):
                current_step = steps[idx]
                step_result = getattr(projection.payload, "test_step_result", None)
                finish_status = getattr(step_result, "status", "") if step_result else ""
                if hasattr(finish_status, "value"):
                    finish_status = finish_status.value
                current_step.status = _map_status(str(finish_status))
                current_step.stop = getattr(projection.payload, "timestamp", 0)
        elif event_type == "test_run_started":
            start_time = getattr(projection.payload, "timestamp", 0)
            if not name:
                name = "Test Run"
        elif event_type == "test_run_finished":
            stop_time = getattr(projection.payload, "timestamp", 0)
            success = getattr(projection.payload, "success", True)
            if not success:
                status = "failed"
            message = getattr(projection.payload, "message", "") or ""
            exception = getattr(projection.payload, "exception", None)
            if exception:
                exc_msg = getattr(exception, "message", "") or ""
                exc_trace = getattr(exception, "stackTrace", "") or getattr(exception, "stack_trace", "") or ""
                if not message:
                    message = exc_msg
                status_details = AllureStatusDetails(message=message, trace=exc_trace)
            elif message:
                status_details = AllureStatusDetails(message=message)
        elif event_type == "test_run_hook_started":
            hook_id = getattr(projection.payload, "hook_id", None)
            if hook_id is None:
                hook_id = getattr(projection.payload, "hookId", None)
            hook_name = _resolve_hook_name(str(hook_id), structural) if hook_id else ""
            if not hook_name:
                hook_name = f"hook:{hook_id}" if hook_id else "run-hook"
            hook_start = getattr(projection.payload, "timestamp", 0)
            step = AllureStepResult(name=hook_name, status="passed", start=hook_start)
            steps.append(step)
        elif event_type == "test_run_hook_finished":
            if steps:
                current_step = steps[-1]
                result = getattr(projection.payload, "result", None)
                if result:
                    finish_status = getattr(result, "status", "") or ""
                    if hasattr(finish_status, "value"):
                        finish_status = finish_status.value
                    current_step.status = _map_status(str(finish_status))
                hook_stop = getattr(projection.payload, "timestamp", 0)
                current_step.stop = hook_stop
        elif event_type == "attachment":
            att_name = getattr(projection.payload, "file_name", None)
            if not att_name:
                att_name = getattr(projection.payload, "media_type", None)
            if not att_name:
                att_name = "attachment"
            att_type = getattr(projection.payload, "media_type", None)
            if not att_type:
                att_type = "text/plain"

            att_source = getattr(projection.payload, "source", "") or ""
            if not isinstance(att_source, str):
                att_source = ""

            body = getattr(projection.payload, "body", None)
            content_encoding = getattr(projection.payload, "content_encoding", None)
            if content_encoding is not None:
                if hasattr(content_encoding, "name"):
                    content_encoding = content_encoding.name
                elif hasattr(content_encoding, "value"):
                    content_encoding = content_encoding.value
                else:
                    content_encoding = str(content_encoding)

            if not att_source and body is not None:
                ext_map = {
                    "text/plain": ".txt",
                    "text/html": ".html",
                    "image/png": ".png",
                    "image/jpeg": ".jpg",
                    "image/gif": ".gif",
                    "application/json": ".json",
                    "application/xml": ".xml",
                    "video/mp4": ".mp4",
                }
                ext = ext_map.get(str(att_type).lower(), ".attach")
                att_source = f"{uuid4()}-attachment{ext}"

            attachment = AllureAttachment(
                name=str(att_name),
                type=str(att_type),
                source=str(att_source),
                body=body,
                content_encoding=content_encoding,
            )
            attachments.append(attachment)
        elif event_type == "fixture":
            fixture_name = getattr(projection.payload, "name", "")
            steps.append(AllureStepResult(name=fixture_name, status="passed"))
        else:
            unmapped_attachment = map_unmappable_to_attachment(projection)
            attachments.append(unmapped_attachment)

    if case_id.startswith("run:"):
        if not name:
            run_id = case_id[4:]
            name = f"Test Run {run_id}"
        if not steps and not attachments:
            status_details = AllureStatusDetails(
                message=status_details.message or "Run-level events only (no test cases executed)",
                trace=status_details.trace,
            )

    result_uuid = str(uuid4()) if case_id.startswith("run:") else case_id

    return AllureTestResult(
        uuid=result_uuid,
        name=name,
        status=status,
        statusDetails=status_details,
        labels=labels,
        links=[],
        steps=steps,
        attachments=attachments,
        parameters=parameters,
        start=start_time,
        stop=stop_time,
    )


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
