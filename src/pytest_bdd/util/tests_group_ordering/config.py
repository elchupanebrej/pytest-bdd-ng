"""
Provides focused utility functions for the `config` concern within pytest-bdd utility layer,
offering helper operatio.

Responsibility:
    Provides focused utility functions for the `config` concern within pytest-bdd utility layer,
    offering helper operations consumed by higher layers (collection, runtime, reporting) without
    pulling in pytest plugin machinery or creating import cycles.

Reason for existence:
    Keeping `config` utilities in a dedicated module prevents cross-cutting helper code from
    accumulating in larger modules where it would create unclear ownership or hidden dependency
    issues. This module is the single authority for `config`-related helper operations within the
    utility layer.

Delegates:
    - Python standard library: delegates core data structure and I/O operations to stdlib

Cohesion:
    All functions and classes serve the single `config` utility concern.

Separation:
    - Sibling utility modules: each handles a distinct helper concern to prevent callers from coupling to unrelated
    functionality.

Main consumers:
    - `pytest_bdd.plugin.*`: imports `config` utilities for reporting, collection, and runtime operations

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

import fnmatch
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from attrs import frozen

if TYPE_CHECKING:
    import pytest


from pytest_bdd.compatibility.tomllib import loads as load_toml

ResolutionSource = Literal["dir_convention", "path_pattern", "conftest_marker", "test_marker", "default"]

_BUILTIN_PYTEST_MARKERS = {
    "filterwarnings",
    "parametrize",
    "skip",
    "skipif",
    "usefixtures",
    "xfail",
}
_FALLBACK_GROUP = "default"
ASSIGNMENT_ATTR = "_pytest_bdd_group_assignment"
ASSIGNMENTS_ATTR = "_pytest_bdd_group_assignments"


@frozen
class GroupPathMapping:
    """
    Encapsulates the GroupPathMapping concern within pytest-bdd, providing a focused set of
    collaborating operations that.

    Responsibility:
        Encapsulates the GroupPathMapping concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        GroupPathMapping is a distinct class because its methods share internal state and collaborate
        on a cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - object: GroupPathMapping specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single GroupPathMapping domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate GroupPathMapping for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of GroupPathMapping maintain internal consistency across all method calls.

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

    pattern: str
    group_name: str


@frozen
class GroupConfig:
    """
    Encapsulates the GroupConfig concern within pytest-bdd, providing a focused set of
    collaborating operations that toge.

    Responsibility:
        Encapsulates the GroupConfig concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        GroupConfig is a distinct class because its methods share internal state and collaborate on a
        cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - object: GroupConfig specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single GroupConfig domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate GroupConfig for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of GroupConfig maintain internal consistency across all method calls.

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
    default: str
    paths: list[GroupPathMapping]
    rootpath: Path


@frozen
class GroupAssignment:
    """
    Encapsulates the GroupAssignment concern within pytest-bdd, providing a focused set of
    collaborating operations that .

    Responsibility:
        Encapsulates the GroupAssignment concern within pytest-bdd, providing a focused set of
        collaborating operations that together deliver a single well-defined capability consumed by the
        broader BDD runtime infrastructure.

    Reason for existence:
        GroupAssignment is a distinct class because its methods share internal state and collaborate on
        a cohesive task that would be awkward to express as standalone functions with shared mutable
        parameters.

    Delegates:
        - object: GroupAssignment specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single GroupAssignment domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate GroupAssignment for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of GroupAssignment maintain internal consistency across all method calls.

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

    item_nodeid: str
    group_name: str
    ordinal: int
    resolution_source: ResolutionSource


@frozen
class RuntimeGroupBarrierObservation:
    """
    Encapsulates the RuntimeGroupBarrierObservation concern within pytest-bdd, providing a focused
    set of collaborating o.

    Responsibility:
        Encapsulates the RuntimeGroupBarrierObservation concern within pytest-bdd, providing a focused
        set of collaborating operations that together deliver a single well-defined capability consumed
        by the broader BDD runtime infrastructure.

    Reason for existence:
        RuntimeGroupBarrierObservation is a distinct class because its methods share internal state and
        collaborate on a cohesive task that would be awkward to express as standalone functions with
        shared mutable parameters.

    Delegates:
        - object: RuntimeGroupBarrierObservation specializes behavior from its parent(s) without duplicating their contracts

    Cohesion:
        All methods and attributes serve the single RuntimeGroupBarrierObservation domain concern.

    Separation:
        - Other types in this module: each class represents a distinct domain within the same layer.

    Main consumers:
        - `pytest_bdd.*`: callers catch or instantiate RuntimeGroupBarrierObservation for error handling and type checking

    State and side effects:
        Holds only instance state directly relevant to its encapsulated concern.

    Invariants:
        - Instances of RuntimeGroupBarrierObservation maintain internal consistency across all method calls.

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

    item_nodeid: str
    group_name: str
    event: Literal["start", "finish"]
    timestamp: float


def _as_list(value: object) -> list[str]:
    """
    Perform the `_as_list` operation within its module boundary, implementing a focused helper.
    function that is consumed.

    Responsibility:
        Performs the `_as_list` operation within its module boundary, implementing a focused helper
        function that is consumed by higher layers for its specific utility purpose within the pytest-
        bdd architecture.

    Reason for existence:
        `_as_list` exists as a standalone function because it encapsulates an operation that does not
        require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _as_list operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _as_list for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _as_list function returns consistent results for equivalent inputs.

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
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _get_ini_value(config: pytest.Config, name: str) -> object:
    """
    Perform the `_get_ini_value` operation within its module boundary, implementing a focused.
    helper function that is co.

    Responsibility:
        Performs the `_get_ini_value` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_get_ini_value` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _get_ini_value operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _get_ini_value for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _get_ini_value function returns consistent results for equivalent inputs.

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
    value = config.getini(name)
    if value not in ("", [], ()):
        return value
    inicfg = getattr(config, "inicfg", {})
    if name in inicfg:
        return inicfg[name]
    pyproject_path = Path(config.rootpath) / "pyproject.toml"
    if pyproject_path.exists():
        pyproject = load_toml(pyproject_path.read_text(encoding="utf-8"))
        pytest_options = pyproject.get("tool", {}).get("pytest", {}).get("ini_options", {})
        if name in pytest_options:
            return pytest_options[name]
    return value


def _normalize_groups(raw_groups: list[str]) -> list[str]:
    """
    Perform the `_normalize_groups` operation within its module boundary, implementing a focused.
    helper function that is.

    Responsibility:
        Performs the `_normalize_groups` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_normalize_groups` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _normalize_groups operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _normalize_groups for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _normalize_groups function returns consistent results for equivalent inputs.

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
    groups: list[str] = []
    seen: set[str] = set()
    for group_name in raw_groups:
        if group_name in seen:
            warnings.warn(
                f"[test-groups] Duplicate group name '{group_name}' found in groups. Duplicate entry ignored.",
                stacklevel=2,
            )
            continue
        if group_name in _BUILTIN_PYTEST_MARKERS:
            warnings.warn(
                f"[test-groups] Group name '{group_name}' shadows a built-in pytest marker. Consider renaming.",
                stacklevel=2,
            )
        seen.add(group_name)
        groups.append(group_name)
    return groups


def _parse_path_mappings(raw_mappings: list[str], groups: list[str]) -> list[GroupPathMapping]:
    """
    Perform the `_parse_path_mappings` operation within its module boundary, implementing a.
    focused helper function that.

    Responsibility:
        Performs the `_parse_path_mappings` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_parse_path_mappings` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _parse_path_mappings operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _parse_path_mappings for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _parse_path_mappings function returns consistent results for equivalent inputs.

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
    mappings: list[GroupPathMapping] = []
    for raw_mapping in raw_mappings:
        if "=" not in raw_mapping:
            warnings.warn(
                f"[test-groups] Malformed path mapping '{raw_mapping}'. Entry ignored.",
                stacklevel=2,
            )
            continue
        pattern, group_name = [part.strip() for part in raw_mapping.split("=", 1)]
        if not pattern or not group_name:
            warnings.warn(
                f"[test-groups] Malformed path mapping '{raw_mapping}'. Entry ignored.",
                stacklevel=2,
            )
            continue
        if group_name not in groups:
            warnings.warn(
                f"[test-groups] Unknown group '{group_name}' in path pattern '{pattern}'. Entry ignored.",
                stacklevel=2,
            )
            continue
        mappings.append(GroupPathMapping(pattern, group_name))
    return mappings


def register_group_config_options(parser: pytest.Parser) -> None:
    """
    Perform the `register_group_config_options` operation within its module boundary, implementing.
    a focused helper func.

    Responsibility:
        Performs the `register_group_config_options` operation within its module boundary, implementing
        a focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `register_group_config_options` exists as a standalone function because it encapsulates an
        operation that does not require shared instance state and benefits from being independently
        callable and testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the register_group_config_options operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke register_group_config_options for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The register_group_config_options function returns consistent results for equivalent inputs.

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
    parser.addini(
        "test_group_order",
        "Ordered pytest test group names; first group runs first.",
        type="args",
        default="",
    )
    parser.addini(
        "test_group_default",
        "Default pytest test group name for unresolved tests.",
        default="",
    )
    parser.addini(
        "test_group_paths",
        "Repo-relative path pattern to group mappings, formatted as 'pattern = group'.",
        type="linelist",
        default="",
    )


def read_group_config(config: pytest.Config) -> GroupConfig:
    """
    Perform the `read_group_config` operation within its module boundary, implementing a focused.
    helper function that is.

    Responsibility:
        Performs the `read_group_config` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `read_group_config` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the read_group_config operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke read_group_config for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The read_group_config function returns consistent results for equivalent inputs.

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
    groups = _normalize_groups(_as_list(_get_ini_value(config, "test_group_order")))
    if not groups:
        warnings.warn(
            "[test-groups] No test groups configured. Using fallback group 'default'.",
            stacklevel=2,
        )
        groups = [_FALLBACK_GROUP]

    default = str(_get_ini_value(config, "test_group_default") or "")
    if default not in groups:
        warnings.warn(
            f"[test-groups] Default group '{default}' not found in groups. Using first group '{groups[0]}'.",
            stacklevel=2,
        )
        default = groups[0]

    paths = _parse_path_mappings(_as_list(_get_ini_value(config, "test_group_paths")), groups)
    return GroupConfig(groups=groups, default=default, paths=paths, rootpath=Path(config.rootpath))


def resolve_path_group(item: pytest.Item, group_config: GroupConfig) -> tuple[str, ResolutionSource]:
    """
    Perform the `resolve_path_group` operation within its module boundary, implementing a focused.
    helper function that i.

    Responsibility:
        Performs the `resolve_path_group` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `resolve_path_group` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the resolve_path_group operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_path_group for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The resolve_path_group function returns consistent results for equivalent inputs.

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
    relative_path = _relative_item_path(item, group_config)
    path_text = relative_path.as_posix()

    matched_group: str | None = None
    for mapping in group_config.paths:
        if fnmatch.fnmatch(path_text, mapping.pattern):
            matched_group = mapping.group_name
    if matched_group is not None:
        return matched_group, "path_pattern"

    path_parts = relative_path.parts
    for group_name in group_config.groups:
        if group_name in path_parts:
            return group_name, "dir_convention"

    return group_config.default, "default"


def resolve_marker_group(item: pytest.Item, group_config: GroupConfig) -> tuple[str, ResolutionSource] | None:
    """
    Perform the `resolve_marker_group` operation within its module boundary, implementing a.
    focused helper function that.

    Responsibility:
        Performs the `resolve_marker_group` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `resolve_marker_group` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the resolve_marker_group operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke resolve_marker_group for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The resolve_marker_group function returns consistent results for equivalent inputs.

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
    conftest_markers: list[str] = []
    test_markers: list[str] = []

    for node, marker in _iter_markers_with_nodes(item):  # type: ignore[attr-defined]  # pytest internal untyped iterator
        marker_name = getattr(marker, "name", "")
        if marker_name not in group_config.groups:
            continue
        source = getattr(node, "source", "")
        if source == "conftest":
            conftest_markers.append(marker_name)
        else:
            test_markers.append(marker_name)

    if test_markers:
        return _latest_group(test_markers, group_config), "test_marker"
    if conftest_markers:
        return _latest_group(conftest_markers, group_config), "conftest_marker"
    return None


def _iter_markers_with_nodes(item: pytest.Item) -> object:
    """
    Perform the `_iter_markers_with_nodes` operation within its module boundary, implementing a.
    focused helper function .

    Responsibility:
        Performs the `_iter_markers_with_nodes` operation within its module boundary, implementing a
        focused helper function that is consumed by higher layers for its specific utility purpose
        within the pytest-bdd architecture.

    Reason for existence:
        `_iter_markers_with_nodes` exists as a standalone function because it encapsulates an operation
        that does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _iter_markers_with_nodes operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _iter_markers_with_nodes for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _iter_markers_with_nodes function returns consistent results for equivalent inputs.

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
    marker_iter = getattr(item, "iter_markers_with_node", None)
    if marker_iter is not None:
        yield from marker_iter()
        return
    for marker in item.iter_markers():
        yield item, marker


def _latest_group(group_names: list[str], group_config: GroupConfig) -> str:
    """
    Perform the `_latest_group` operation within its module boundary, implementing a focused.
    helper function that is con.

    Responsibility:
        Performs the `_latest_group` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_latest_group` exists as a standalone function because it encapsulates an operation that does
        not require shared instance state and benefits from being independently callable and testable
        without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _latest_group operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _latest_group for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _latest_group function returns consistent results for equivalent inputs.

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
    return max(group_names, key=group_config.groups.index)


def _relative_item_path(item: pytest.Item, group_config: GroupConfig) -> Path:
    """
    Perform the `_relative_item_path` operation within its module boundary, implementing a focused.
    helper function that .

    Responsibility:
        Performs the `_relative_item_path` operation within its module boundary, implementing a focused
        helper function that is consumed by higher layers for its specific utility purpose within the
        pytest-bdd architecture.

    Reason for existence:
        `_relative_item_path` exists as a standalone function because it encapsulates an operation that
        does not require shared instance state and benefits from being independently callable and
        testable without class instantiation overhead.

    Delegates:
        - Python standard library: delegates core operations to stdlib

    Cohesion:
        All logic directly supports the _relative_item_path operation.

    Separation:
        - Other functions in this module: each function handles a distinct helper concern.

    Main consumers:
        - `pytest_bdd.*`: callers import and invoke _relative_item_path for its specific utility

    State and side effects:
        None, this function is stateless and produces its output purely from input arguments.

    Invariants:
        - The _relative_item_path function returns consistent results for equivalent inputs.

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
    item_path = Path(getattr(item, "path", getattr(item, "fspath", "")))
    if not item_path.is_absolute():
        return item_path
    try:
        return item_path.relative_to(group_config.rootpath)
    except ValueError:
        return item_path
