"""
Status priority helpers for step execution policies.

Responsibility:
    Status priority helpers for step execution policies. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.plugin.pickle_runner.status_policy` because it keeps the
    nearest code, data shape, call signature, and failure knowledge together.

Delegates:
    - StatusPolicy: owns nested behavior below this boundary
    - TolerantStatusPolicy: owns nested behavior below this boundary
    - normalize_wip_status: owns nested behavior below this boundary
    - _status_from_item_marker: owns nested behavior below this boundary
    - normalize_tolerant_status: owns nested behavior below this boundary
    - _status_from_tag_markers: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - None found by static import/name scan; verify dynamic use before refactor

State and side effects:
    mutates value, source, normalized, marker, name; depends on __future__.annotations, typing.TYPE_CHECKING,
    typing.Literal, attrs, pytest_bdd.compatibility.pytest.Item.

Invariants:
    - `pytest_bdd.plugin.pickle_runner.status_policy` keeps its documented import path, ownership boundary, and
      observable behavior stable for callers.

Architecture score:
    #arch-eval:reason_for_existence=4
    #arch-eval:owned_responsibility=4
    #arch-eval:delegation_boundary=4
    #arch-eval:cohesion=3
    #arch-eval:separation=3
    #arch-eval:consumer_clarity=2
    #arch-eval:state_invariants=4
    #arch-eval:entity_fullness=4
    #arch-eval:locational_stability=2
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import attrs

if TYPE_CHECKING:
    from pytest_bdd.compatibility.pytest import Item

WipStatus = Literal["passed", "skipped", "failed"]
TolerantStatus = Literal["failed", "ignored"]
WIP_STATUSES: tuple[WipStatus, ...] = ("passed", "skipped", "failed")
TOLERANT_STATUSES: tuple[TolerantStatus, ...] = ("failed", "ignored")


@attrs.define(frozen=True)
class StatusPolicy:
    """
    Resolved status policy value.

    Responsibility:
        Resolved status policy value. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.status_policy.StatusPolicy` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - attrs.define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates value, source.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy.StatusPolicy` keeps its documented import path, ownership
          boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    value: WipStatus
    source: str


@attrs.define(frozen=True)
class TolerantStatusPolicy:
    """
    Resolved tolerant status policy value.

    Responsibility:
        Resolved tolerant status policy value. It directly owns the observable contract, local decisions, and
        maintenance boundary for this class. That boundary is intentionally stated in prose so maintainers can
        distinguish owned work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.status_policy.TolerantStatusPolicy`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - attrs.define: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates value, source.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy.TolerantStatusPolicy` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=2
    """

    value: TolerantStatus
    source: str


def normalize_wip_status(value: object) -> WipStatus | None:
    """
    Normalize a raw WIP status value.

    Args:
        value: Raw status value.

    Returns:
        WIP status or None when unsupported.

    Responsibility:
        Normalize a raw WIP status value. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.status_policy.normalize_wip_status`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str.strip.lower.replace: collaborator call used by this boundary
        - str.strip.lower: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates normalized.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy.normalize_wip_status` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    normalized = str(value).strip().lower().replace("_", "-")
    if normalized in WIP_STATUSES:
        return normalized  # str literal matches WipStatus union
    return None


def _status_from_item_marker(item: Item) -> WipStatus | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.status_policy._status_from_item_marker` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.status_policy._status_from_item_marker` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - next: collaborator call used by this boundary
        - item.iter_markers: collaborator call used by this boundary
        - normalize_wip_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates marker.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy._status_from_item_marker` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    marker = next(item.iter_markers(name="wip_status"), None)
    if marker is None or not marker.args:
        return None
    return normalize_wip_status(marker.args[0])


def normalize_tolerant_status(value: object) -> TolerantStatus | None:
    """
    Normalize a raw tolerant status value.

    Args:
        value: Raw status value.

    Returns:
        Tolerant status or None when unsupported.

    Responsibility:
        Normalize a raw tolerant status value. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.status_policy.normalize_tolerant_status` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - str.strip.lower.replace: collaborator call used by this boundary
        - str.strip.lower: collaborator call used by this boundary
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates normalized.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy.normalize_tolerant_status` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2

    """
    normalized = str(value).strip().lower().replace("_", "-")
    if normalized in TOLERANT_STATUSES:
        return normalized  # str literal matches TolerantStatus union
    return None


def _status_from_tag_markers(item: Item) -> WipStatus | None:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.plugin.pickle_runner.status_policy._status_from_tag_markers` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.status_policy._status_from_tag_markers` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - item.iter_markers: collaborator call used by this boundary
        - marker.name.replace: collaborator call used by this boundary
        - name.startswith: collaborator call used by this boundary
        - normalize_wip_status: collaborator call used by this boundary
        - name.removeprefix: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates name, prefix.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy._status_from_tag_markers` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    for marker in item.iter_markers():
        name = marker.name.replace("_", "-")
        prefix = "wip-status-"
        if name.startswith(prefix):
            return normalize_wip_status(name.removeprefix(prefix))
    return None


def _tolerant_status_from_item_marker(item: Item) -> TolerantStatus | None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.pickle_runner.status_policy._tolerant_status_from_item_marker` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.status_policy._tolerant_status_from_item_marker` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - next: collaborator call used by this boundary
        - item.iter_markers: collaborator call used by this boundary
        - normalize_tolerant_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates marker.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy._tolerant_status_from_item_marker` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    marker = next(item.iter_markers(name="tolerant_status"), None)
    if marker is None or not marker.args:
        return None
    return normalize_tolerant_status(marker.args[0])


def _tolerant_status_from_tag_markers(item: Item) -> TolerantStatus | None:
    """
    Responsibility:
        Responsibility: Responsibility:
        `pytest_bdd.plugin.pickle_runner.status_policy._tolerant_status_from_tag_markers` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.status_policy._tolerant_status_from_tag_markers` because it keeps the nearest
        code, data shape, call signature, and failure knowledge together.

    Delegates:
        - item.iter_markers: collaborator call used by this boundary
        - marker.name.replace: collaborator call used by this boundary
        - name.startswith: collaborator call used by this boundary
        - normalize_tolerant_status: collaborator call used by this boundary
        - name.removeprefix: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - None found by static import/name scan; verify dynamic use before refactor

    State and side effects:
        mutates name, prefix.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy._tolerant_status_from_tag_markers` keeps its documented import
          path, ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=4
        #arch-eval:cohesion=4
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=2
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=4
        #arch-eval:locational_stability=2
    """
    for marker in item.iter_markers():
        name = marker.name.replace("_", "-")
        prefix = "tolerant-status-"
        if name.startswith(prefix):
            return normalize_tolerant_status(name.removeprefix(prefix))
    return None


def resolve_wip_status(item: Item, cli_status: object, default: WipStatus = "failed") -> StatusPolicy:
    """
    Resolve WIP status using marker > tag > CLI > default priority.

    Args:
        item: Pytest item.
        cli_status: CLI option value.
        default: Default status.

    Returns:
        Resolved status policy.

    Responsibility:
        Resolve WIP status using marker > tag > CLI > default priority. It directly owns the observable contract, local
        decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.plugin.pickle_runner.status_policy.resolve_wip_status`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - StatusPolicy: collaborator call used by this boundary
        - _status_from_item_marker: collaborator call used by this boundary
        - _status_from_tag_markers: collaborator call used by this boundary
        - normalize_wip_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_wip_status`

    State and side effects:
        mutates marker_status, tag_status, cli_wip_status.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy.resolve_wip_status` keeps its documented import path, ownership
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
    marker_status = _status_from_item_marker(item)
    if marker_status is not None:
        return StatusPolicy(value=marker_status, source="pytest-marker")

    tag_status = _status_from_tag_markers(item)
    if tag_status is not None:
        return StatusPolicy(value=tag_status, source="gherkin-tag")

    cli_wip_status = normalize_wip_status(cli_status)
    if cli_wip_status is not None:
        return StatusPolicy(value=cli_wip_status, source="cli")

    return StatusPolicy(value=default, source="default")


def resolve_tolerant_status(
    item: Item,
    cli_status: object,
    default: TolerantStatus = "failed",
) -> TolerantStatusPolicy:
    """
    Resolve tolerant status using marker > tag > CLI > default priority.

    Args:
        item: Pytest item.
        cli_status: CLI option value.
        default: Default status.

    Returns:
        Resolved tolerant status policy.

    Responsibility:
        Resolve tolerant status using marker > tag > CLI > default priority. It directly owns the observable contract,
        local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.plugin.pickle_runner.status_policy.resolve_tolerant_status` because it keeps the nearest code, data
        shape, call signature, and failure knowledge together.

    Delegates:
        - TolerantStatusPolicy: collaborator call used by this boundary
        - _tolerant_status_from_item_marker: collaborator call used by this boundary
        - _tolerant_status_from_tag_markers: collaborator call used by this boundary
        - normalize_tolerant_status: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/pickle_runner/plugin/_executor.py: imports or references `resolve_tolerant_status`

    State and side effects:
        mutates marker_status, tag_status, cli_tolerant_status.

    Invariants:
        - `pytest_bdd.plugin.pickle_runner.status_policy.resolve_tolerant_status` keeps its documented import path,
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
    marker_status = _tolerant_status_from_item_marker(item)
    if marker_status is not None:
        return TolerantStatusPolicy(value=marker_status, source="pytest-marker")

    tag_status = _tolerant_status_from_tag_markers(item)
    if tag_status is not None:
        return TolerantStatusPolicy(value=tag_status, source="gherkin-tag")

    cli_tolerant_status = normalize_tolerant_status(cli_status)
    if cli_tolerant_status is not None:
        return TolerantStatusPolicy(value=cli_tolerant_status, source="cli")

    return TolerantStatusPolicy(value=default, source="default")
