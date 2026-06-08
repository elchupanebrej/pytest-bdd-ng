"""
Test group barrier synchronization helpers for xdist.

Responsibility:
    Test group barrier synchronization helpers for xdist. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - _BarrierState: owns nested behavior below this boundary
    - _coerce_string_list: owns nested behavior below this boundary
    - _coerce_int_mapping: owns nested behavior below this boundary
    - _replace_with_retry: owns nested behavior below this boundary
    - write_barrier_state: owns nested behavior below this boundary
    - read_barrier_state_once: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `barrier`
    - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `barrier`

State and side effects:
    mutates state, expected, finished, state_path, groups; depends on __future__.annotations, json, logging, os, time.

Invariants:
    - `pytest_bdd.util.tests_group_ordering.barrier` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Failure semantics:
    Raises or re-raises re-raise, TimeoutError; callers must treat these as boundary failures.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=4
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=3
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._BarrierState` owns documented
        class behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        class.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._BarrierState` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_BarrierState`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_BarrierState`

    State and side effects:
        mutates groups, expected, finished, finished_nodeids.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._BarrierState` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=3
    """

    groups: list[str]
    expected: dict[str, int]
    finished: dict[str, int]
    finished_nodeids: list[str]


def _coerce_string_list(value: object) -> list[str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._coerce_string_list` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._coerce_string_list`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_coerce_string_list`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_coerce_string_list`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _coerce_int_mapping(value: object) -> dict[str, int]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._coerce_int_mapping` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._coerce_int_mapping`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - isinstance: collaborator call used by this boundary
        - value.items: collaborator call used by this boundary
        - int: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_coerce_int_mapping`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_coerce_int_mapping`

    State and side effects:
        mutates result.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._coerce_int_mapping` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._replace_with_retry` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._replace_with_retry`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - range: collaborator call used by this boundary
        - temp_path.replace: collaborator call used by this boundary
        - time.sleep: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_replace_with_retry`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_replace_with_retry`

    State and side effects:
        mutates attempts.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._replace_with_retry` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    attempts = 50
    for attempt in range(attempts):
        try:
            temp_path.replace(state_path)
        except (PermissionError, OSError):  # noqa: PERF203
            if attempt == attempts - 1:
                raise
            time.sleep(0.01)
        else:
            break


def write_barrier_state(state_path: Path, state: _BarrierState) -> None:
    """
    Write barrier state to a file.

    Responsibility:
        Write barrier state to a file. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier.write_barrier_state`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - state_path.with_suffix: collaborator call used by this boundary
        - os.getpid: collaborator call used by this boundary
        - temp_path.write_text: collaborator call used by this boundary
        - json.dumps: collaborator call used by this boundary
        - _replace_with_retry: collaborator call used by this boundary
        - logger.warning: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `write_barrier_state`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `write_barrier_state`

    State and side effects:
        mutates temp_path.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier.write_barrier_state` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Read barrier state from a file once.

    Args:
        state_path: Path to the barrier state file.

    Returns:
        Barrier state dictionary or None if decoding failed.

    Responsibility:
        Read barrier state from a file once. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier.read_barrier_state_once`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - payload.get: collaborator call used by this boundary
        - _coerce_string_list: collaborator call used by this boundary
        - _coerce_int_mapping: collaborator call used by this boundary
        - json.loads: collaborator call used by this boundary
        - state_path.read_text: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `read_barrier_state_once`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `read_barrier_state_once`

    State and side effects:
        mutates payload.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier.read_barrier_state_once` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Read barrier state from a file with retry logic.

    Args:
        state_path: Path to the barrier state file.

    Returns:
        Barrier state dictionary.

    Raises:
        PermissionError: If the file cannot be accessed.
        OSError: If an OS error occurs.

    Responsibility:
        Read barrier state from a file with retry logic. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier.read_barrier_state`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - time.sleep: collaborator call used by this boundary
        - state_path.exists: collaborator call used by this boundary
        - range: collaborator call used by this boundary
        - read_barrier_state_once: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `read_barrier_state`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `read_barrier_state`

    State and side effects:
        mutates attempts, state.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier.read_barrier_state` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises re-raise; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if not state_path.exists():
        return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}

    attempts = 50
    for attempt in range(attempts):
        try:
            state = read_barrier_state_once(state_path)
        except (PermissionError, OSError):  # noqa: PERF203
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._barrier_lock` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._barrier_lock` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - state_path.with_suffix: collaborator call used by this boundary
        - lock_path.mkdir: collaborator call used by this boundary
        - time.sleep: collaborator call used by this boundary
        - suppress: collaborator call used by this boundary
        - lock_path.rmdir: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_barrier_lock`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_barrier_lock`

    State and side effects:
        mutates lock_path.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._barrier_lock` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._initialize_barrier_state` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.tests_group_ordering.barrier._initialize_barrier_state` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - _barrier_lock: collaborator call used by this boundary
        - state_path.exists: collaborator call used by this boundary
        - dict.fromkeys: collaborator call used by this boundary
        - write_barrier_state: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_initialize_barrier_state`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_initialize_barrier_state`

    State and side effects:
        mutates state.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._initialize_barrier_state` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._previous_groups_finished` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.tests_group_ordering.barrier._previous_groups_finished` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - int: collaborator call used by this boundary
        - finished.get: collaborator call used by this boundary
        - expected.get: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_previous_groups_finished`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_previous_groups_finished`

    State and side effects:
        mutates groups, expected, finished.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._previous_groups_finished` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._record_barrier_finish` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._record_barrier_finish`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _barrier_lock: collaborator call used by this boundary
        - read_barrier_state: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - int: collaborator call used by this boundary
        - finished.get: collaborator call used by this boundary
        - finished_nodeids.add: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_record_barrier_finish`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_record_barrier_finish`

    State and side effects:
        mutates state, finished_nodeids, finished.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier._record_barrier_finish` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.barrier._is_terminal_report` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier._is_terminal_report`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - cast: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_is_terminal_report`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_is_terminal_report`

    State and side effects:
        keeps no local persistent state beyond call-local values.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=3
        #arch-eval:entity_fullness=4
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
    Configure runtime barrier state for xdist execution.

    Responsibility:
        Configure runtime barrier state for xdist execution. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.tests_group_ordering.barrier.configure_runtime_barrier` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - hasattr: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - config.workerinput.get: collaborator call used by this boundary
        - state_path.parent.mkdir: collaborator call used by this boundary
        - dict.fromkeys: collaborator call used by this boundary
        - assignments.values: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `configure_runtime_barrier`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `configure_runtime_barrier`

    State and side effects:
        mutates run_uid, state_path, expected.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier.configure_runtime_barrier` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Handle wait for group barrier.

    Raises:
        TimeoutError: If the operation cannot be completed.

    Responsibility:
        Handle wait for group barrier. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.barrier.wait_for_group_barrier`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - time.monotonic: collaborator call used by this boundary
        - float: collaborator call used by this boundary
        - os.environ.get: collaborator call used by this boundary
        - read_barrier_state: collaborator call used by this boundary
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `wait_for_group_barrier`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `wait_for_group_barrier`

    State and side effects:
        mutates assignment, state_path, timeout, deadline, state.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier.wait_for_group_barrier` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Failure semantics:
        Raises or re-raises TimeoutError; callers must treat these as boundary failures.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
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
    Handle record group barrier report.

    Responsibility:
        Handle record group barrier report. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.tests_group_ordering.barrier.record_group_barrier_report` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - _is_terminal_report: collaborator call used by this boundary
        - _RUNTIME_BARRIER_STATE_PATHS.get: collaborator call used by this boundary
        - _RUNTIME_BARRIER_ASSIGNMENTS.get: collaborator call used by this boundary
        - _record_barrier_finish: collaborator call used by this boundary
        - Path: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `record_group_barrier_report`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `record_group_barrier_report`

    State and side effects:
        mutates state_path, assignment.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.barrier.record_group_barrier_report` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=3
    """
    if not _is_terminal_report(report):
        return
    state_path = _RUNTIME_BARRIER_STATE_PATHS.get(report.nodeid)
    assignment = _RUNTIME_BARRIER_ASSIGNMENTS.get(report.nodeid)
    if state_path is None or assignment is None:
        return
    _record_barrier_finish(Path(state_path), assignment)
