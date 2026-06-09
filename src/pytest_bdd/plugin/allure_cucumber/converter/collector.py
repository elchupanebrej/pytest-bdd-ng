"""Group cucumber message projections by test case."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_bdd.model.execution_message_adapter import ExecutionProjection

# Type alias for the structural context dictionary.
# Keys are tuples of (kind, id) where kind is "pickle", "test_case", or "hook".
StructuralContext = dict[tuple[str, str], object]


def _index_structural_message(
    projection: ExecutionProjection,
    structural: StructuralContext,
) -> None:
    """Index a structural message (pickle, testCase, hook) in the context dictionary."""
    event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))
    if event_type == "pickle":
        msg_id = getattr(projection.payload, "id", None)
        if msg_id is not None:
            structural["pickle", str(msg_id)] = projection.payload
    elif event_type == "test_case":
        msg_id = getattr(projection.payload, "id", None)
        if msg_id is not None:
            structural["test_case", str(msg_id)] = projection.payload
    elif event_type == "hook":
        msg_id = getattr(projection.payload, "id", None)
        if msg_id is not None:
            structural["hook", str(msg_id)] = projection.payload


def group_by_test_case(
    projections: Iterable[ExecutionProjection],
) -> tuple[dict[str, list[ExecutionProjection]], StructuralContext]:
    """
    Group envelope projections by testCaseStartedId or testRunStartedId.

    Each TestCaseStarted/TestStepStarted/Attachment event references
    a testCaseStartedId. Group them under that ID for per-scenario processing.

    Run-level events (testRunStarted, testRunHookStarted/Finished,
    testRunFinished) are grouped under a synthetic "run:{run_id}" key
    so they produce at least one Allure result.

    Structural messages (pickle, testCase, hook) are indexed in a side-channel
    context dictionary for the mapper to resolve names via lookup chains.

    Returns:
        Tuple of (grouped projections dict, structural context dict).

    """
    projection_list = list(projections)
    hook_started_by_id: dict[str, ExecutionProjection] = {}
    structural: StructuralContext = {}
    last_run_id: str | None = None

    for proj in projection_list:
        event_type = getattr(proj.payload_kind, "value", str(proj.payload_kind))
        if event_type == "test_run_hook_started":
            hook_id = getattr(proj.payload, "id", None)
            if hook_id is not None:
                hook_started_by_id[str(hook_id)] = proj

        # Track last run ID for test_run_finished fallback
        if event_type == "test_run_started":
            run_id = getattr(proj.payload, "id", None)
            if run_id is not None:
                last_run_id = str(run_id)

        _index_structural_message(proj, structural)

    by_case: dict[str, list[ExecutionProjection]] = defaultdict(list)
    for projection in projection_list:
        case_id = _extract_test_case_id(projection)
        if case_id is not None:
            by_case[case_id].append(projection)
            continue
        run_id = _extract_run_id(projection, hook_started_by_id)
        if run_id is not None:
            by_case[f"run:{run_id}"].append(projection)
            continue
        # Fallback: test_run_finished without testRunStartedId → use last known run ID
        event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))
        if event_type == "test_run_finished" and last_run_id is not None:
            by_case[f"run:{last_run_id}"].append(projection)
    return dict(by_case), structural


def _extract_test_case_id(projection: ExecutionProjection) -> str | None:
    """
    Get testCaseStartedId from projection payload.

    For TestCaseStarted events, the ID is in the `id` field.
    For other events, it's in `testCaseStartedId`.

    Returns:
        The test case ID string, or None if not found.

    """
    raw = getattr(projection.payload, "test_case_started_id", None)
    if raw is None:
        raw = getattr(projection.payload, "testCaseStartedId", None)
    if raw is None and getattr(projection.payload_kind, "value", str(projection.payload_kind)) == "test_case_started":
        raw = getattr(projection.payload, "id", None)
    return str(raw) if raw is not None else None


def _extract_run_id(
    projection: ExecutionProjection,
    hook_started_by_id: dict[str, ExecutionProjection],
) -> str | None:
    """
    Extract testRunStartedId from run-level events.

    For testRunStarted events, the ID is in the `id` field.
    For testRunHookStarted/testRunFinished, it's in `testRunStartedId`.
    For testRunHookFinished, resolve through testRunHookStartedId → testRunHookStarted → testRunStartedId.

    Returns:
        The run ID string, or None if not a run-level event.

    """
    event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))
    if event_type == "test_run_started":
        return str(getattr(projection.payload, "id", "")) or None
    raw = getattr(projection.payload, "test_run_started_id", None)
    if raw is None:
        raw = getattr(projection.payload, "testRunStartedId", None)
    if raw is not None:
        return str(raw)
    if event_type == "test_run_hook_finished":
        hook_started_id = getattr(projection.payload, "test_run_hook_started_id", None)
        if hook_started_id is None:
            hook_started_id = getattr(projection.payload, "testRunHookStartedId", None)
        if hook_started_id is not None:
            hook_started_proj = hook_started_by_id.get(str(hook_started_id))
            if hook_started_proj is not None:
                hook_run_id = getattr(hook_started_proj.payload, "test_run_started_id", None)
                if hook_run_id is None:
                    hook_run_id = getattr(hook_started_proj.payload, "testRunStartedId", None)
                if hook_run_id is not None:
                    return str(hook_run_id)
    return None
