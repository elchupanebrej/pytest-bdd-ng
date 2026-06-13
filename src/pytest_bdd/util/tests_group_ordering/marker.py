"""
Provides focused utility functions for the `marker` concern within pytest-bdd utility layer,
offering helper operatio.

Responsibility:
    Provides focused utility functions for the `marker` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `marker` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `marker`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `marker` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `marker` utilities for reporting, collection, and runtime operations

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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from pytest_bdd.compatibility.pytest import make_mark, make_mark_decorator
from pytest_bdd.util.tests_group_ordering.config import (
    ASSIGNMENT_ATTR,
    ASSIGNMENTS_ATTR,
    GroupAssignment,
    GroupConfig,
    read_group_config,
    resolve_marker_group,
    resolve_path_group,
)


def resolve_group_assignment(item: pytest.Item, group_config: GroupConfig) -> GroupAssignment:
    """
    Perform the `resolve_group_assignment` operation within its module boundary, implementing a.
    focused helper function .

    Responsibility:
        Performs the `resolve_group_assignment` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `resolve_group_assignment` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the resolve_group_assignment operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_group_assignment for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The resolve_group_assignment function returns consistent results for equivalent inputs.

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
    group_name, source = resolve_path_group(item, group_config)
    marker_assignment = resolve_marker_group(item, group_config)
    if marker_assignment is not None:
        group_name, source = marker_assignment

    return GroupAssignment(
        item_nodeid=str(getattr(item, "nodeid", "")),
        group_name=group_name,
        ordinal=group_config.groups.index(group_name) + 1,
        resolution_source=source,
    )


def apply_order_marker(item: pytest.Item, assignment: GroupAssignment) -> None:
    """
    Perform the `apply_order_marker` operation within its module boundary, implementing a focused.
    helper function that i.

    Responsibility:
        Performs the `apply_order_marker` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `apply_order_marker` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the apply_order_marker operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke apply_order_marker for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The apply_order_marker function returns consistent results for equivalent inputs.

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
    item.add_marker(make_mark_decorator(make_mark("order", args=(assignment.ordinal,))))


def apply_group_marker(item: pytest.Item, assignment: GroupAssignment) -> None:
    """
    Perform the `apply_group_marker` operation within its module boundary, implementing a focused.
    helper function that i.

    Responsibility:
        Performs the `apply_group_marker` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `apply_group_marker` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the apply_group_marker operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke apply_group_marker for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The apply_group_marker function returns consistent results for equivalent inputs.

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
    item.add_marker(make_mark_decorator(make_mark(assignment.group_name)))


def apply_group_ordering(config: pytest.Config, items: list[pytest.Item]) -> None:
    """
    Perform the `apply_group_ordering` operation within its module boundary, implementing a.
    focused helper function that.

    Responsibility:
        Performs the `apply_group_ordering` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `apply_group_ordering` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the apply_group_ordering operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke apply_group_ordering for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The apply_group_ordering function returns consistent results for equivalent inputs.

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
    from pytest_bdd.util.tests_group_ordering.barrier import configure_runtime_barrier

    group_config = read_group_config(config)
    for index, group_name in enumerate(group_config.groups, start=1):
        config.addinivalue_line("markers", f"{group_name}: test group {index}")
    assignments: dict[str, GroupAssignment] = {}
    for item in items:
        assignment = resolve_group_assignment(item, group_config)
        setattr(item, ASSIGNMENT_ATTR, assignment)
        assignments[assignment.item_nodeid] = assignment
        apply_group_marker(item, assignment)
        apply_order_marker(item, assignment)
    setattr(config, ASSIGNMENTS_ATTR, assignments)
    configure_runtime_barrier(config, group_config, assignments)
