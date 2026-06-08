"""
Test group marker application helpers.

Responsibility:
    Test group marker application helpers. It directly owns the observable contract, local decisions, and maintenance
    boundary for this module. That boundary is intentionally stated in prose so maintainers can distinguish owned work
    from collaborators before editing.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.tests_group_ordering.marker` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - resolve_group_assignment: owns nested behavior below this boundary
    - apply_order_marker: owns nested behavior below this boundary
    - apply_group_marker: owns nested behavior below this boundary
    - apply_group_ordering: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/plugin/pickle_runner/status_policy.py: imports or references `marker`
    - src/pytest_bdd/util/tests_group_ordering/config.py: imports or references `marker`
    - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `marker`

State and side effects:
    mutates group_name, source, marker_assignment, group_config, assignments; depends on __future__.annotations,
    typing.TYPE_CHECKING, pytest, pytest_bdd.compatibility.pytest.make_mark,
    pytest_bdd.compatibility.pytest.make_mark_decorator.

Invariants:
    - `pytest_bdd.util.tests_group_ordering.marker` keeps its documented import path, ownership boundary, and observable
      behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
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
    Resolve group assignment for a test item.

    Args:
        item: Pytest test item.
        group_config: Group configuration.

    Returns:
        Group assignment for the item.

    Responsibility:
        Resolve group assignment for a test item. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.marker.resolve_group_assignment`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - resolve_path_group: collaborator call used by this boundary
        - resolve_marker_group: collaborator call used by this boundary
        - GroupAssignment: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - group_config.groups.index: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `resolve_group_assignment`

    State and side effects:
        mutates group_name, source, marker_assignment.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.marker.resolve_group_assignment` keeps its documented import path,
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
    Apply order marker.

    Responsibility:
        Apply order marker. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.marker.apply_order_marker`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - item.add_marker: collaborator call used by this boundary
        - make_mark_decorator: collaborator call used by this boundary
        - make_mark: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `apply_order_marker`

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
    item.add_marker(make_mark_decorator(make_mark("order", args=(assignment.ordinal,))))


def apply_group_marker(item: pytest.Item, assignment: GroupAssignment) -> None:
    """
    Apply group marker.

    Responsibility:
        Apply group marker. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.marker.apply_group_marker`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - item.add_marker: collaborator call used by this boundary
        - make_mark_decorator: collaborator call used by this boundary
        - make_mark: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `apply_group_marker`

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
    item.add_marker(make_mark_decorator(make_mark(assignment.group_name)))


def apply_group_ordering(config: pytest.Config, items: list[pytest.Item]) -> None:
    """
    Apply group ordering.

    Responsibility:
        Apply group ordering. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.marker.apply_group_ordering`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - setattr: collaborator call used by this boundary
        - read_group_config: collaborator call used by this boundary
        - enumerate: collaborator call used by this boundary
        - config.addinivalue_line: collaborator call used by this boundary
        - resolve_group_assignment: collaborator call used by this boundary
        - apply_group_marker: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `apply_group_ordering`

    State and side effects:
        mutates group_config, assignments, assignment; depends on
        pytest_bdd.util.tests_group_ordering.barrier.configure_runtime_barrier.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.marker.apply_group_ordering` keeps its documented import path, ownership
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
    from pytest_bdd.util.tests_group_ordering.barrier import configure_runtime_barrier  # noqa: PLC0415

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
