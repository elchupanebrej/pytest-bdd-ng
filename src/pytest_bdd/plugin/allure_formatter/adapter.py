"""Adapter to map Cucumber Message projections to allure-python-commons lifecycle."""

from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import allure_commons
from allure_commons.lifecycle import AllureLifecycle
from allure_commons.logger import AllureFileLogger
from allure_commons.model2 import (
    Label,
    Link,
    Parameter,
    StatusDetails,
    TestResult,
    TestResultContainer,
    TestStepResult,
)

from pytest_bdd.plugin.allure_formatter.converter.collector import group_by_test_case
from pytest_bdd.plugin.allure_formatter.converter.mapper import map_test_case_to_result

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from pytest_bdd.model.execution_message_adapter import ExecutionProjection
    from pytest_bdd.plugin.allure_formatter.converter.model import (
        AllureAttachment,
        AllureStepResult,
        AllureTestResult,
    )

logger = logging.getLogger(__name__)


def to_ms(timestamp: Any) -> int | None:
    """Convert a timestamp to integer milliseconds."""
    if timestamp is None:
        return None
    # 1. Check if it's a Cucumber messages/deserialized Timestamp object
    if hasattr(timestamp, "seconds") and hasattr(timestamp, "nanos"):
        return int(timestamp.seconds * 1000 + timestamp.nanos / 1000000)
    # 2. Check if it is a dictionary (e.g. JSON representation of Timestamp)
    if isinstance(timestamp, dict):
        seconds = timestamp.get("seconds", 0)
        nanos = timestamp.get("nanos", 0)
        return int(seconds * 1000 + nanos / 1000000)
    # 3. Check if it's already an int or float
    if isinstance(timestamp, (int, float)):
        if timestamp == 0:
            return 0
        if timestamp > 1e11:
            return int(timestamp)
        return int(timestamp * 1000)
    return None


def convert_to_allure_commons(projections: Iterable[ExecutionProjection], output_dir: Path) -> None:
    """Convert Cucumber Message projections and write Allure3 JSON results using allure-python-commons."""
    grouped, structural = group_by_test_case(projections)

    results: list[AllureTestResult] = []
    for case_id, case_projections in grouped.items():
        if case_id.startswith("run:"):
            continue
        result = map_test_case_to_result(case_id, case_projections, structural)
        results.append(result)

    if not results:
        return

    # Initialize AllureLifecycle
    lifecycle = AllureLifecycle()

    # Create and register the file logger
    file_logger = AllureFileLogger(str(output_dir))
    allure_commons.plugin_manager.register(file_logger)

    try:
        # Write results
        result_uuids = []
        for res in results:
            write_result(res, lifecycle)
            result_uuids.append(res.uuid)

        # Write container
        container = TestResultContainer(
            uuid=str(uuid4()),
            name="Test results",
            children=result_uuids,
        )
        allure_commons.plugin_manager.hook.report_container(container=container)
    finally:
        # Always unregister the logger so we don't leak it
        allure_commons.plugin_manager.unregister(file_logger)


def write_result(res: AllureTestResult, lifecycle: AllureLifecycle) -> None:
    """Write an AllureTestResult tree to the lifecycle."""
    status_details = StatusDetails(
        message=res.statusDetails.message,
        trace=res.statusDetails.trace,
        known=res.statusDetails.known,
        flaky=res.statusDetails.flaky,
    )

    labels = [Label(name=lbl.name, value=lbl.value) for lbl in res.labels]
    links = [Link(type=lnk.type, url=lnk.url, name=lnk.name) for lnk in res.links]
    parameters = [Parameter(name=p.name, value=p.value, excluded=p.excluded, mode=p.mode) for p in res.parameters]

    test_result = TestResult(
        uuid=res.uuid,
        name=res.name,
        fullName=res.fullName,
        historyId=res.historyId,
        testCaseId=res.testCaseId,
        status=res.status,
        statusDetails=status_details,
        stage=res.stage,
        description=res.description,
        descriptionHtml=res.descriptionHtml,
        labels=labels,
        links=links,
        parameters=parameters,
        start=to_ms(res.start),
        stop=to_ms(res.stop),
    )

    # Place in items map
    lifecycle._items[test_result.uuid] = test_result

    # Reconstruct Steps and Attachments recursively
    for step in res.steps:
        add_step_to_parent(step, test_result, lifecycle)

    # Add attachments at test result level
    for att in res.attachments:
        write_attachment(att, test_result.uuid, lifecycle)

    # Write test case
    lifecycle.write_test_case(test_result.uuid)


def add_step_to_parent(
    step: AllureStepResult,
    parent: Any,
    lifecycle: AllureLifecycle,
) -> None:
    """Recursively add a step to parent step or test case."""
    step_details = StatusDetails(
        message=step.statusDetails.message,
        trace=step.statusDetails.trace,
        known=step.statusDetails.known,
        flaky=step.statusDetails.flaky,
    )
    step_parameters = [Parameter(name=p.name, value=p.value, excluded=p.excluded, mode=p.mode) for p in step.parameters]
    step_result = TestStepResult(
        name=step.name,
        status=step.status,
        statusDetails=step_details,
        stage=step.stage,
        description=step.description,
        descriptionHtml=step.descriptionHtml,
        parameters=step_parameters,
        start=to_ms(step.start),
        stop=to_ms(step.stop),
    )

    parent.steps.append(step_result)
    step_uuid = step.uuid or str(uuid4())

    # Temporarily register in items so attachment parenting works
    lifecycle._items[step_uuid] = step_result

    for substep in step.steps:
        add_step_to_parent(substep, step_result, lifecycle)

    for att in step.attachments:
        write_attachment(att, step_uuid, lifecycle)

    # Pop the step from items
    lifecycle._items.pop(step_uuid, None)


def write_attachment(
    att: AllureAttachment,
    parent_uuid: str,
    lifecycle: AllureLifecycle,
) -> None:
    """Write an attachment to parent executable item."""
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
    ext = ext_map.get(str(att.type).lower(), "attach")

    if att.body is not None:
        body_str = att.body
        body_str = body_str.get("data", "") or "" if isinstance(body_str, dict) else str(body_str or "")

        attachment_uuid = str(uuid4())

        if str(att.content_encoding).upper() == "BASE64":
            try:
                body_bytes = base64.b64decode(body_str)
                lifecycle.attach_data(
                    uuid=attachment_uuid,
                    body=body_bytes,
                    name=att.name,
                    attachment_type=att.type,
                    extension=ext,
                    parent_uuid=parent_uuid,
                )
            except Exception:
                lifecycle.attach_data(
                    uuid=attachment_uuid,
                    body=body_str,
                    name=att.name,
                    attachment_type=att.type,
                    extension=ext,
                    parent_uuid=parent_uuid,
                )
        else:
            lifecycle.attach_data(
                uuid=attachment_uuid,
                body=body_str,
                name=att.name,
                attachment_type=att.type,
                extension=ext,
                parent_uuid=parent_uuid,
            )
    elif att.source:
        attachment_uuid = str(uuid4())
        lifecycle.attach_file(
            uuid=attachment_uuid,
            source=att.source,
            name=att.name,
            attachment_type=att.type,
            extension=ext,
            parent_uuid=parent_uuid,
        )
