"""
Provides focused utility functions for the `barrier` concern within pytest-bdd utility layer,
offering helper operati.

Responsibility:
    Provides focused utility functions for the `barrier` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `barrier` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `barrier`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `barrier` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `barrier` utilities for reporting, collection, and runtime operations

State and side effects:
    None, this module keeps no persistent state and performs no file or network I/O.

Invariants:
    - The public API surface (exported names) remains stable across internal refactors.

Architecture score:
    #arch-eval:reason_for_existence=5
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=4
    #arch-eval:separation=4
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=4
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest

from pytest_bdd.util.tests_group_ordering.config import (
    ASSIGNMENT_ATTR,
    GroupAssignment,
    GroupConfig,
)

_BARRIER_STATE_ATTR = "_pytest_bdd_group_barrier_state_path"
_BARRIER_LOCK_POLL_SECONDS = 0.01
_BARRIER_WAIT_POLL_SECONDS = 0.02
_BARRIER_TIMEOUT_SECONDS = 60.0
_RUNTIME_BARRIER_STATE_PATHS: dict[str, Path] = {}
_RUNTIME_BARRIER_ASSIGNMENTS: dict[str, GroupAssignment] = {}
logger = logging.getLogger(__name__)


class _BarrierState(TypedDict):
    """
    Encapsulates the _BarrierState concern within pytest-bdd, providing a focused set of
    collaborating operations that to.

    Responsibility:
        Encapsulates the _BarrierState concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        _BarrierState is a distinct class because its methods share internal state and collaborate on a
        cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - TypedDict: _BarrierState specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single _BarrierState domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate _BarrierState for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of _BarrierState maintain internal consistency across all method calls.

    Architecture score:
        #arch-eval:reason_for_existence=5
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=5
        #arch-eval:separation=4
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4
    """

    groups: list[str]
    expected: dict[str, int]
    finished: dict[str, int]
    finished_nodeids: list[str]


def _coerce_string_list(value: object) -> list[str]:
    """
    Perform the `_coerce_string_list` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `_coerce_string_list` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_coerce_string_list` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _coerce_string_list operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _coerce_string_list for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _coerce_string_list function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _coerce_int_mapping(value: object) -> dict[str, int]:
    """
    Perform the `_coerce_int_mapping` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `_coerce_int_mapping` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_coerce_int_mapping` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _coerce_int_mapping operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _coerce_int_mapping for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _coerce_int_mapping function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            continue
        try:
            result[key] = int(item)
        except (TypeError, ValueError):
            continue
    return result


def _replace_with_retry(temp_path: Path, state_path: Path) -> None:
    """
    Perform the `_replace_with_retry` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `_replace_with_retry` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_replace_with_retry` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _replace_with_retry operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _replace_with_retry for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _replace_with_retry function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    attempts = 50
    for attempt in range(attempts):
        try:
            temp_path.replace(state_path)
        except (PermissionError, OSError):  # noqa: PERF203  -- suppressed warning
            if attempt == attempts - 1:
                raise
            time.sleep(0.01)
        else:
            break


def write_barrier_state(state_path: Path, state: _BarrierState) -> None:
    """
    Perform the `write_barrier_state` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `write_barrier_state` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `write_barrier_state` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the write_barrier_state operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke write_barrier_state for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The write_barrier_state function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    temp_path = state_path.with_suffix(f".{os.getpid()}.tmp")
    temp_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    try:
        _replace_with_retry(temp_path, state_path)
    except Exception:
        logger.warning("Failed to replace test-group barrier state file", exc_info=True)
        with suppress(FileNotFoundError):
            temp_path.unlink()
        raise


def read_barrier_state_once(state_path: Path) -> _BarrierState | None:
    """
    Perform the `read_barrier_state_once` operation within its module boundary, implementing a.
    focused helper function t.

    Responsibility:
        Performs the `read_barrier_state_once` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `read_barrier_state_once` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the read_barrier_state_once operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke read_barrier_state_once for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The read_barrier_state_once function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}
    return {
        "groups": _coerce_string_list(payload.get("groups")),
        "expected": _coerce_int_mapping(payload.get("expected")),
        "finished": _coerce_int_mapping(payload.get("finished")),
        "finished_nodeids": _coerce_string_list(payload.get("finished_nodeids")),
    }


def read_barrier_state(state_path: Path) -> _BarrierState:
    """
    Perform the `read_barrier_state` operation within its module boundary, implementing a focused.
    helper function that i.

    Responsibility:
        Performs the `read_barrier_state` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `read_barrier_state` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the read_barrier_state operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke read_barrier_state for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The read_barrier_state function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not state_path.exists():
        return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}

    attempts = 50
    for attempt in range(attempts):
        try:
            state = read_barrier_state_once(state_path)
        except (PermissionError, OSError):  # noqa: PERF203  -- suppressed warning
            if attempt == attempts - 1:
                raise
            time.sleep(0.01)
        else:
            if state is not None:
                return state
            time.sleep(0.01)

    return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}


@contextmanager
def _barrier_lock(state_path: Path) -> Iterator[None]:
    """
    Perform the `_barrier_lock` operation within its module boundary, implementing a focused.
    helper function that is con.

    Responsibility:
        Performs the `_barrier_lock` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_barrier_lock` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _barrier_lock operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _barrier_lock for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _barrier_lock function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    lock_path = state_path.with_suffix(".lock")
    while True:
        try:
            lock_path.mkdir()
            break
        except FileExistsError:
            time.sleep(_BARRIER_LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        with suppress(FileNotFoundError):
            lock_path.rmdir()


def _initialize_barrier_state(state_path: Path, groups: list[str], expected: dict[str, int]) -> None:
    """
    Perform the `_initialize_barrier_state` operation within its module boundary, implementing a.
    focused helper function.

    Responsibility:
        Performs the `_initialize_barrier_state` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_initialize_barrier_state` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _initialize_barrier_state operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _initialize_barrier_state for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _initialize_barrier_state function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    with _barrier_lock(state_path):
        if state_path.exists():
            return
        state: _BarrierState = {
            "groups": groups,
            "expected": expected,
            "finished": dict.fromkeys(groups, 0),
            "finished_nodeids": [],
        }
        write_barrier_state(
            state_path,
            state,
        )


def _previous_groups_finished(state: _BarrierState, assignment: GroupAssignment) -> bool:
    """
    Perform the `_previous_groups_finished` operation within its module boundary, implementing a.
    focused helper function.

    Responsibility:
        Performs the `_previous_groups_finished` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_previous_groups_finished` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _previous_groups_finished operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _previous_groups_finished for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _previous_groups_finished function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    groups = state["groups"]
    expected = state["expected"]
    finished = state["finished"]
    for group_name in groups[: assignment.ordinal - 1]:
        if int(finished.get(group_name, 0)) < int(expected.get(group_name, 0)):
            return False
    return True


def _record_barrier_finish(state_path: Path, assignment: GroupAssignment) -> None:
    """
    Perform the `_record_barrier_finish` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `_record_barrier_finish` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_record_barrier_finish` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _record_barrier_finish operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _record_barrier_finish for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _record_barrier_finish function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    with _barrier_lock(state_path):
        state = read_barrier_state(state_path)
        finished_nodeids = set(state["finished_nodeids"])
        if assignment.item_nodeid in finished_nodeids:
            return
        finished = state["finished"]
        finished[assignment.group_name] = int(finished.get(assignment.group_name, 0)) + 1
        finished_nodeids.add(assignment.item_nodeid)
        state["finished"] = finished
        state["finished_nodeids"] = sorted(finished_nodeids)
        write_barrier_state(state_path, state)


def _is_terminal_report(report: pytest.TestReport) -> bool:
    """
    Perform the `_is_terminal_report` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `_is_terminal_report` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_is_terminal_report` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _is_terminal_report operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _is_terminal_report for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _is_terminal_report function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if report.when == "call":
        return True
    return cast("bool", report.when == "setup" and (report.failed or report.skipped))


def configure_runtime_barrier(
    config: pytest.Config,
    group_config: GroupConfig,
    assignments: dict[str, GroupAssignment],
) -> None:
    """
    Perform the `configure_runtime_barrier` operation within its module boundary, implementing a.
    focused helper function.

    Responsibility:
        Performs the `configure_runtime_barrier` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `configure_runtime_barrier` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the configure_runtime_barrier operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke configure_runtime_barrier for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The configure_runtime_barrier function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not hasattr(config, "workerinput"):
        return
    run_uid = str(config.workerinput.get("testrunuid") or "default")  # upstream type stubs missing this attribute
    state_path = config.rootpath / ".pytest_cache" / "pytest-bdd-test-groups" / run_uid / "barrier.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    expected = dict.fromkeys(group_config.groups, 0)
    for assignment in assignments.values():
        expected[assignment.group_name] += 1
    _initialize_barrier_state(state_path, group_config.groups, expected)
    setattr(config, _BARRIER_STATE_ATTR, state_path)
    for nodeid, assignment in assignments.items():
        _RUNTIME_BARRIER_STATE_PATHS[nodeid] = state_path
        _RUNTIME_BARRIER_ASSIGNMENTS[nodeid] = assignment


def wait_for_group_barrier(item: pytest.Item) -> None:
    """
    Perform the `wait_for_group_barrier` operation within its module boundary, implementing a.
    focused helper function th.

    Responsibility:
        Performs the `wait_for_group_barrier` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `wait_for_group_barrier` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the wait_for_group_barrier operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke wait_for_group_barrier for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The wait_for_group_barrier function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    assignment = getattr(item, ASSIGNMENT_ATTR, None)
    state_path = getattr(item.config, _BARRIER_STATE_ATTR, None)
    if assignment is None or state_path is None:
        return

    timeout = float(os.environ.get("PYTEST_BDD_TEST_GROUP_BARRIER_TIMEOUT", _BARRIER_TIMEOUT_SECONDS))
    deadline = time.monotonic() + timeout
    while True:
        state = read_barrier_state(Path(state_path))
        if _previous_groups_finished(state, assignment):
            return
        if time.monotonic() >= deadline:
            message = (
                f"Timed out waiting for earlier test groups before {assignment.item_nodeid!r} "
                f"in group {assignment.group_name!r}."
            )
            raise TimeoutError(message)
        time.sleep(_BARRIER_WAIT_POLL_SECONDS)


def record_group_barrier_report(report: pytest.TestReport) -> None:
    """
    Perform the `record_group_barrier_report` operation within its module boundary, implementing a.
    focused helper functi.

    Responsibility:
        Performs the `record_group_barrier_report` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `record_group_barrier_report` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the record_group_barrier_report operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke record_group_barrier_report for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The record_group_barrier_report function returns consistent results for equivalent inputs.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=3
        #arch-eval:delegation_boundary=3
        #arch-eval:cohesion=5
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=3
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=3
        #arch-eval:locational_stability=3
    """
    if not _is_terminal_report(report):
        return
    state_path = _RUNTIME_BARRIER_STATE_PATHS.get(report.nodeid)
    assignment = _RUNTIME_BARRIER_ASSIGNMENTS.get(report.nodeid)
    if state_path is None or assignment is None:
        return
    _record_barrier_finish(Path(state_path), assignment)
