"""Reconstruct hierarchical step tree from flat TestStepStarted/Finished pairs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pytest_bdd.model.execution_message_adapter import ExecutionProjection


def build_step_tree(
    projections: list[ExecutionProjection],
) -> list[dict[str, Any]]:
    """
    Build a nested step hierarchy from flat cucumber message events.

    Uses a stack-based approach:
    1. TestStepStarted → push step onto current branch's stack
    2. TestStepFinished → pop from stack, attach to parent
    3. Track testStepId → parent via pickle_step_id references

    Returns:
        List of root-level step dictionaries with nested 'steps' children.

    """
    stack: list[dict[str, Any]] = []
    root_steps: list[dict[str, Any]] = []
    step_map: dict[str, dict[str, Any]] = {}

    for projection in projections:
        event_type = getattr(projection.payload_kind, "value", str(projection.payload_kind))

        if event_type == "TestStepStarted":
            step: dict[str, Any] = {
                "name": getattr(projection.payload, "name", ""),
                "steps": [],
            }
            step_id = str(getattr(projection.payload, "test_step_id", ""))
            step_map[step_id] = step

            if stack:
                stack[-1]["steps"].append(step)
            else:
                root_steps.append(step)

            stack.append(step)

        elif event_type == "TestStepFinished":
            if stack:
                finished_step = stack.pop()
                status = getattr(projection.payload, "status", "unknown")
                finished_step["status"] = status
                if hasattr(projection.payload, "status_details"):
                    finished_step["status_details"] = getattr(projection.payload, "status_details", {})
                if hasattr(projection.payload, "duration"):
                    finished_step["duration"] = getattr(projection.payload, "duration", 0)

        elif event_type == "TestCaseStarted":
            root_steps.append(
                {
                    "name": "Test Case",
                    "steps": [],
                },
            )
            stack.append(root_steps[-1])

    return root_steps
