"""
Runtime identifier and lifecycle-reference helpers for BDD model objects.

These utilities are defined in the MODEL layer because they operate purely on
model-layer types (LifecycleKind, LifecycleObjectRef, FixtureRequest) and do
not depend on any plugin or runtime internals.  They were previously located
in plugin/pickle_runner/run_transitions.py — a downward dependency violation —
and are now imported from there for backward compatibility.

Responsibility:
    Runtime identifier and lifecycle-reference helpers for BDD model objects. It directly owns the observable contract,
    local decisions, and maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.model.run.transitions` because it keeps the nearest code, data
    shape, call signature, and failure knowledge together.

Delegates:
    - runtime_object_id: owns nested behavior below this boundary
    - runtime_object_name: owns nested behavior below this boundary
    - build_lifecycle_ref: owns nested behavior below this boundary
    - initial_scenario_run_id: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/model/run/__init__.py: imports or references `transitions`
    - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `transitions`
    - src/pytest_bdd/model/run_access.py: imports or references `transitions`
    - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `transitions`

State and side effects:
    mutates name, _context_index, explicit_id, nodeid, ast_node_ids; depends on __future__.annotations, itertools.count,
    typing.TYPE_CHECKING, returns.maybe.Nothing, pytest_bdd.model.run.refs.LifecycleKind.

Invariants:
    - `pytest_bdd.model.run.transitions` keeps its documented import path, ownership boundary, and observable behavior
      stable for callers.

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

from itertools import count
from typing import TYPE_CHECKING

from returns.maybe import Nothing

from pytest_bdd.model.run.refs import LifecycleKind, LifecycleObjectRef

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import FixtureRequest

_context_index = count(1)


def runtime_object_id(obj: object) -> str:
    """
    Get runtime object ID.

    Args:
        obj: Object to get ID for.

    Returns:
        String representation of object ID.

    Responsibility:
        Get runtime object ID. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.transitions.runtime_object_id` because it keeps
        the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - id: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `runtime_object_id`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `runtime_object_id`
        - src/pytest_bdd/model/run_access.py: imports or references `runtime_object_id`
        - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `runtime_object_id`

    State and side effects:
        mutates explicit_id, nodeid, name, ast_node_ids.

    Invariants:
        - `pytest_bdd.model.run.transitions.runtime_object_id` keeps its documented import path, ownership boundary, and
          observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    if obj is None:
        return "none"
    explicit_id = getattr(obj, "id", None)
    if explicit_id is not None:
        return str(explicit_id)
    nodeid = getattr(obj, "nodeid", None)
    if nodeid is not None:
        return str(nodeid)
    name = getattr(obj, "name", None)
    if name is not None:
        return str(name)
    ast_node_ids = getattr(obj, "ast_node_ids", None)
    if ast_node_ids:
        return str(ast_node_ids[0])
    return str(id(obj))


def runtime_object_name(obj: object) -> str | None:
    """
    Get runtime object name.

    Args:
        obj: Object to get name for.

    Returns:
        Name string or None.

    Responsibility:
        Get runtime object name. It directly owns the observable contract, local decisions, and maintenance boundary for
        this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.transitions.runtime_object_name` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `runtime_object_name`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `runtime_object_name`
        - src/pytest_bdd/model/run_access.py: imports or references `runtime_object_name`
        - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `runtime_object_name`

    State and side effects:
        mutates name.

    Invariants:
        - `pytest_bdd.model.run.transitions.runtime_object_name` keeps its documented import path, ownership boundary,
          and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=4

    """
    if obj is None:
        return Nothing.value_or(None)
    name = getattr(obj, "name", None)
    return str(name) if name is not None else None


def build_lifecycle_ref(kind: LifecycleKind, value: object, *, is_active: bool) -> LifecycleObjectRef | None:
    """
    Build a lifecycle reference.

    Args:
        kind: Lifecycle kind.
        value: Object to reference.
        is_active: Whether the object is active.

    Returns:
        LifecycleObjectRef or None.

    Responsibility:
        Build a lifecycle reference. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.transitions.build_lifecycle_ref` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - Nothing.value_or: collaborator call used by this boundary
        - LifecycleObjectRef: collaborator call used by this boundary
        - runtime_object_id: collaborator call used by this boundary
        - runtime_object_name: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `build_lifecycle_ref`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `build_lifecycle_ref`
        - src/pytest_bdd/model/run_access.py: imports or references `build_lifecycle_ref`
        - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `build_lifecycle_ref`

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
        #arch-eval:locational_stability=4

    """
    if value is None:
        return Nothing.value_or(None)
    return LifecycleObjectRef(
        kind=kind,
        object_id=runtime_object_id(value),
        name=runtime_object_name(value),
        source=value.__class__.__name__,
        is_active=is_active,
    )


def initial_scenario_run_id(request: FixtureRequest) -> str:
    """
    Get initial scenario run ID.

    Args:
        request: Pytest fixture request.

    Returns:
        Initial scenario run ID string.

    Responsibility:
        Get initial scenario run ID. It directly owns the observable contract, local decisions, and maintenance boundary
        for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned work from
        collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.model.run.transitions.initial_scenario_run_id` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - next: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/model/run/__init__.py: imports or references `initial_scenario_run_id`
        - src/pytest_bdd/model/run/lifecycle/_run.py: imports or references `initial_scenario_run_id`
        - src/pytest_bdd/model/run_access.py: imports or references `initial_scenario_run_id`
        - src/pytest_bdd/plugin/pickle_runner/run_transitions.py: imports or references `initial_scenario_run_id`

    State and side effects:
        mutates node_id, key.

    Invariants:
        - `pytest_bdd.model.run.transitions.initial_scenario_run_id` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4

    """
    node_id = getattr(getattr(request, "node", None), "nodeid", None)
    key = node_id or f"unknown-{next(_context_index)}"
    return f"ctx-{key}-{next(_context_index)}"
