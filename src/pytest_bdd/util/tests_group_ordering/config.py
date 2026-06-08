"""
Test group config parsing and resolution helpers.

Responsibility:
    Test group config parsing and resolution helpers. It directly owns the observable contract, local decisions, and
    maintenance boundary for this module.

Reason for existence:
    This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config` because it keeps the nearest
    code, data shape, call signature, and failure knowledge together.

Delegates:
    - GroupPathMapping: owns nested behavior below this boundary
    - GroupConfig: owns nested behavior below this boundary
    - GroupAssignment: owns nested behavior below this boundary
    - RuntimeGroupBarrierObservation: owns nested behavior below this boundary
    - _as_list: owns nested behavior below this boundary
    - _get_ini_value: owns nested behavior below this boundary

Cohesion:
    The implementation stays together because its imports, calls, state writes, and return contract describe one
    maintainable decision unit.

Separation:
    - module peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
      widening caller knowledge.

Main consumers:
    - src/pytest_bdd/_pylint/checkers/layer_rules.py: imports or references `config`
    - src/pytest_bdd/collector.py: imports or references `config`
    - src/pytest_bdd/compatibility/pytest/__init__.py: imports or references `config`
    - src/pytest_bdd/feature_locator.py: imports or references `config`
    - src/pytest_bdd/hook.py: imports or references `config`

State and side effects:
    mutates group_name, groups, default, pattern, paths; depends on __future__.annotations, fnmatch, warnings,
    pathlib.Path, typing.TYPE_CHECKING.

Invariants:
    - `pytest_bdd.util.tests_group_ordering.config` keeps its documented import path, ownership boundary, and observable
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
    Represent group path mapping state.

    Responsibility:
        Represent group path mapping state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config.GroupPathMapping` because
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
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `GroupPathMapping`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `GroupPathMapping`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `GroupPathMapping`

    State and side effects:
        mutates pattern, group_name.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.GroupPathMapping` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """

    pattern: str
    group_name: str


@frozen
class GroupConfig:
    """
    Represent group config state.

    Responsibility:
        Represent group config state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config.GroupConfig` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `GroupConfig`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `GroupConfig`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `GroupConfig`

    State and side effects:
        mutates groups, default, paths, rootpath.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.GroupConfig` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """

    groups: list[str]
    default: str
    paths: list[GroupPathMapping]
    rootpath: Path


@frozen
class GroupAssignment:
    """
    Represent group assignment state.

    Responsibility:
        Represent group assignment state. It directly owns the observable contract, local decisions, and maintenance
        boundary for this class. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config.GroupAssignment` because
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
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `GroupAssignment`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `GroupAssignment`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `GroupAssignment`

    State and side effects:
        mutates item_nodeid, group_name, ordinal, resolution_source.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.GroupAssignment` keeps its documented import path, ownership
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
        #arch-eval:locational_stability=4
    """

    item_nodeid: str
    group_name: str
    ordinal: int
    resolution_source: ResolutionSource


@frozen
class RuntimeGroupBarrierObservation:
    """
    Represent runtime group barrier observation state.

    Responsibility:
        Represent runtime group barrier observation state. It directly owns the observable contract, local decisions,
        and maintenance boundary for this class.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.tests_group_ordering.config.RuntimeGroupBarrierObservation` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - None, leaf-level implementation boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - class peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable without
          widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `RuntimeGroupBarrierObservation`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `RuntimeGroupBarrierObservation`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `RuntimeGroupBarrierObservation`

    State and side effects:
        mutates item_nodeid, group_name, event, timestamp.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.RuntimeGroupBarrierObservation` keeps its documented import path,
          ownership boundary, and observable behavior stable for callers.

    Architecture score:
        #arch-eval:reason_for_existence=4
        #arch-eval:owned_responsibility=4
        #arch-eval:delegation_boundary=2
        #arch-eval:cohesion=3
        #arch-eval:separation=3
        #arch-eval:consumer_clarity=4
        #arch-eval:state_invariants=4
        #arch-eval:entity_fullness=2
        #arch-eval:locational_stability=4
    """

    item_nodeid: str
    group_name: str
    event: Literal["start", "finish"]
    timestamp: float


def _as_list(value: object) -> list[str]:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._as_list` owns documented function
        behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._as_list` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - str.strip: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - isinstance: collaborator call used by this boundary
        - line.strip: collaborator call used by this boundary
        - value.splitlines: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_as_list`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_as_list`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_as_list`

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
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _get_ini_value(config: pytest.Config, name: str) -> object:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._get_ini_value` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._get_ini_value` because
        it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - config.getini: collaborator call used by this boundary
        - getattr: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - pyproject_path.exists: collaborator call used by this boundary
        - load_toml: collaborator call used by this boundary
        - pyproject_path.read_text: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_get_ini_value`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_get_ini_value`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_get_ini_value`

    State and side effects:
        mutates value, inicfg, pyproject_path, pyproject, pytest_options.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config._get_ini_value` keeps its documented import path, ownership
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._normalize_groups` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._normalize_groups`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - warnings.warn: collaborator call used by this boundary
        - set: collaborator call used by this boundary
        - seen.add: collaborator call used by this boundary
        - groups.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_normalize_groups`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_normalize_groups`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_normalize_groups`

    State and side effects:
        mutates groups, seen.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config._normalize_groups` keeps its documented import path, ownership
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._parse_path_mappings` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._parse_path_mappings`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - warnings.warn: collaborator call used by this boundary
        - part.strip: collaborator call used by this boundary
        - raw_mapping.split: collaborator call used by this boundary
        - mappings.append: collaborator call used by this boundary
        - GroupPathMapping: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_parse_path_mappings`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_parse_path_mappings`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_parse_path_mappings`

    State and side effects:
        mutates mappings, pattern, group_name.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config._parse_path_mappings` keeps its documented import path, ownership
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
    Register group config options.

    Responsibility:
        Register group config options. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function. That boundary is intentionally stated in prose so maintainers can distinguish owned
        work from collaborators before editing.

    Reason for existence:
        This entity is the information expert for
        `pytest_bdd.util.tests_group_ordering.config.register_group_config_options` because it keeps the nearest code,
        data shape, call signature, and failure knowledge together.

    Delegates:
        - parser.addini: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/plugin/test_group_ordering/entrypoint.py: imports or references `register_group_config_options`
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `register_group_config_options`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `register_group_config_options`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `register_group_config_options`

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
    Read test group configuration from pytest config.

    Args:
        config: Pytest config object.

    Returns:
        Group configuration object.

    Responsibility:
        Read test group configuration from pytest config. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config.read_group_config`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _get_ini_value: collaborator call used by this boundary
        - _as_list: collaborator call used by this boundary
        - warnings.warn: collaborator call used by this boundary
        - _normalize_groups: collaborator call used by this boundary
        - str: collaborator call used by this boundary
        - _parse_path_mappings: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `read_group_config`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `read_group_config`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `read_group_config`

    State and side effects:
        mutates groups, default, paths.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.read_group_config` keeps its documented import path, ownership
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
    Resolve the group for an item based on its path.

    Args:
        item: Pytest test item.
        group_config: Group configuration.

    Returns:
        Tuple of group name and resolution source.

    Responsibility:
        Resolve the group for an item based on its path. It directly owns the observable contract, local decisions, and
        maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config.resolve_path_group`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - _relative_item_path: collaborator call used by this boundary
        - relative_path.as_posix: collaborator call used by this boundary
        - fnmatch.fnmatch: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `resolve_path_group`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `resolve_path_group`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `resolve_path_group`

    State and side effects:
        mutates matched_group, relative_path, path_text, path_parts.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.resolve_path_group` keeps its documented import path, ownership
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
    Resolve the group for an item based on its markers.

    Args:
        item: Pytest test item.
        group_config: Group configuration.

    Returns:
        Tuple of group name and resolution source, or None if no group marker is found.

    Responsibility:
        Resolve the group for an item based on its markers. It directly owns the observable contract, local decisions,
        and maintenance boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config.resolve_marker_group`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - _latest_group: collaborator call used by this boundary
        - _iter_markers_with_nodes: collaborator call used by this boundary
        - conftest_markers.append: collaborator call used by this boundary
        - test_markers.append: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `resolve_marker_group`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `resolve_marker_group`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `resolve_marker_group`

    State and side effects:
        mutates conftest_markers, test_markers, marker_name, source.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config.resolve_marker_group` keeps its documented import path, ownership
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
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._iter_markers_with_nodes` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._iter_markers_with_nodes`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - marker_iter: collaborator call used by this boundary
        - item.iter_markers: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_iter_markers_with_nodes`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_iter_markers_with_nodes`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_iter_markers_with_nodes`

    State and side effects:
        mutates marker_iter.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config._iter_markers_with_nodes` keeps its documented import path,
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
        #arch-eval:locational_stability=4
    """
    marker_iter = getattr(item, "iter_markers_with_node", None)
    if marker_iter is not None:
        yield from marker_iter()
        return
    for marker in item.iter_markers():
        yield item, marker


def _latest_group(group_names: list[str], group_config: GroupConfig) -> str:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._latest_group` owns documented
        function behavior. It directly owns the observable contract, local decisions, and maintenance boundary for this
        function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._latest_group` because it
        keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - max: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_latest_group`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_latest_group`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_latest_group`

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
    return max(group_names, key=group_config.groups.index)


def _relative_item_path(item: pytest.Item, group_config: GroupConfig) -> Path:
    """
    Responsibility:
        Responsibility: Responsibility: `pytest_bdd.util.tests_group_ordering.config._relative_item_path` owns
        documented function behavior. It directly owns the observable contract, local decisions, and maintenance
        boundary for this function.

    Reason for existence:
        This entity is the information expert for `pytest_bdd.util.tests_group_ordering.config._relative_item_path`
        because it keeps the nearest code, data shape, call signature, and failure knowledge together.

    Delegates:
        - getattr: collaborator call used by this boundary
        - Path: collaborator call used by this boundary
        - item_path.is_absolute: collaborator call used by this boundary
        - item_path.relative_to: collaborator call used by this boundary

    Cohesion:
        The implementation stays together because its imports, calls, state writes, and return contract describe one
        maintainable decision unit.

    Separation:
        - call-site peer: remains separate so same-kind responsibilities stay discoverable, testable, and changeable
          without widening caller knowledge.

    Main consumers:
        - src/pytest_bdd/util/tests_group_ordering/barrier.py: imports or references `_relative_item_path`
        - src/pytest_bdd/util/tests_group_ordering/facade.py: imports or references `_relative_item_path`
        - src/pytest_bdd/util/tests_group_ordering/marker.py: imports or references `_relative_item_path`

    State and side effects:
        mutates item_path.

    Invariants:
        - `pytest_bdd.util.tests_group_ordering.config._relative_item_path` keeps its documented import path, ownership
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
    item_path = Path(getattr(item, "path", getattr(item, "fspath", "")))
    if not item_path.is_absolute():
        return item_path
    try:
        return item_path.relative_to(group_config.rootpath)
    except ValueError:
        return item_path
