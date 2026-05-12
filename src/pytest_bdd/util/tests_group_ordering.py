"""Provide tests group ordering helpers."""

from __future__ import annotations

import fnmatch
import json
import os
import time
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict

from attrs import frozen
from returns.maybe import Nothing

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest

from pytest_bdd.compatibility.pytest import Mark, MarkDecorator
from pytest_bdd.compatibility.tomllib import loads as load_toml

ResolutionSource = Literal["dir_convention", "path_pattern", "conftest_marker", "test_marker", "default"]


@frozen
class GroupPathMapping:
    """Represent group path mapping state."""

    pattern: str
    group_name: str


@frozen
class GroupConfig:
    """Represent group config state."""

    groups: list[str]
    default: str
    paths: list[GroupPathMapping]
    rootpath: Path


@frozen
class GroupAssignment:
    """Represent group assignment state."""

    item_nodeid: str
    group_name: str
    ordinal: int
    resolution_source: ResolutionSource


@frozen
class RuntimeGroupBarrierObservation:
    """Represent runtime group barrier observation state."""

    item_nodeid: str
    group_name: str
    event: Literal["start", "finish"]
    timestamp: float


class _BarrierState(TypedDict):
    groups: list[str]
    expected: dict[str, int]
    finished: dict[str, int]
    finished_nodeids: list[str]


_BUILTIN_PYTEST_MARKERS = {
    "filterwarnings",
    "parametrize",
    "skip",
    "skipif",
    "usefixtures",
    "xfail",
}
_FALLBACK_GROUP = "default"
_ASSIGNMENT_ATTR = "_pytest_bdd_group_assignment"
_ASSIGNMENTS_ATTR = "_pytest_bdd_group_assignments"
_BARRIER_STATE_ATTR = "_pytest_bdd_group_barrier_state_path"
_BARRIER_LOCK_POLL_SECONDS = 0.01
_BARRIER_WAIT_POLL_SECONDS = 0.02
_BARRIER_TIMEOUT_SECONDS = 60.0
_RUNTIME_BARRIER_STATE_PATHS: dict[str, Path] = {}
_RUNTIME_BARRIER_ASSIGNMENTS: dict[str, GroupAssignment] = {}


def register_group_config_options(parser: pytest.Parser) -> None:
    """Register group config options."""
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


def resolve_group_assignment(item: pytest.Item, group_config: GroupConfig) -> GroupAssignment:
    """
    Resolve group assignment for a test item.

    Args:
        item: Pytest test item.
        group_config: Group configuration.

    Returns:
        Group assignment for the item.

    """
    group_name, source = _resolve_path_group(item, group_config)
    marker_assignment = _resolve_marker_group(item, group_config)
    if marker_assignment is not None:
        group_name, source = marker_assignment

    return GroupAssignment(
        item_nodeid=str(getattr(item, "nodeid", "")),
        group_name=group_name,
        ordinal=group_config.groups.index(group_name) + 1,
        resolution_source=source,
    )


def apply_order_marker(item: pytest.Item, assignment: GroupAssignment) -> None:
    """Apply order marker."""
    item.add_marker(
        MarkDecorator(
            Mark("order", args=(assignment.ordinal,), kwargs={}, _ispytest=True),
            _ispytest=True,
        ),
    )


def apply_group_marker(item: pytest.Item, assignment: GroupAssignment) -> None:
    """Apply group marker."""
    item.add_marker(
        MarkDecorator(
            Mark(assignment.group_name, args=(), kwargs={}, _ispytest=True),
            _ispytest=True,
        ),
    )


def apply_group_ordering(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Apply group ordering."""
    group_config = read_group_config(config)
    for index, group_name in enumerate(group_config.groups, start=1):
        config.addinivalue_line("markers", f"{group_name}: test group {index}")
    assignments: dict[str, GroupAssignment] = {}
    for item in items:
        assignment = resolve_group_assignment(item, group_config)
        setattr(item, _ASSIGNMENT_ATTR, assignment)
        assignments[assignment.item_nodeid] = assignment
        apply_group_marker(item, assignment)
        apply_order_marker(item, assignment)
    setattr(config, _ASSIGNMENTS_ATTR, assignments)
    _configure_runtime_barrier(config, group_config, assignments)


def wait_for_group_barrier(item: pytest.Item) -> None:
    """
    Handle wait for group barrier.

    Raises:
        TimeoutError: If the operation cannot be completed.

    """
    assignment = getattr(item, _ASSIGNMENT_ATTR, None)
    state_path = getattr(item.config, _BARRIER_STATE_ATTR, None)
    if assignment is None or state_path is None:
        return

    timeout = float(os.environ.get("PYTEST_BDD_TEST_GROUP_BARRIER_TIMEOUT", _BARRIER_TIMEOUT_SECONDS))
    deadline = time.monotonic() + timeout
    while True:
        state = _read_barrier_state(Path(state_path))
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
    """Handle record group barrier report."""
    if not _is_terminal_report(report):
        return
    state_path = _RUNTIME_BARRIER_STATE_PATHS.get(report.nodeid)
    assignment = _RUNTIME_BARRIER_ASSIGNMENTS.get(report.nodeid)
    if state_path is None or assignment is None:
        return
    _record_barrier_finish(Path(state_path), assignment)


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _get_ini_value(config: pytest.Config, name: str) -> object:
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


def _resolve_path_group(item: pytest.Item, group_config: GroupConfig) -> tuple[str, ResolutionSource]:
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


def _resolve_marker_group(item: pytest.Item, group_config: GroupConfig) -> tuple[str, ResolutionSource] | None:
    conftest_markers: list[str] = []
    test_markers: list[str] = []

    for node, marker in _iter_markers_with_nodes(item):
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
    return Nothing.value_or(None)


def _iter_markers_with_nodes(item: pytest.Item) -> Iterator[tuple[pytest.Item, Mark]]:
    marker_iter = getattr(item, "iter_markers_with_node", None)
    if marker_iter is not None:
        yield from marker_iter()
        return
    for marker in item.iter_markers():
        yield item, marker


def _latest_group(group_names: list[str], group_config: GroupConfig) -> str:
    return max(group_names, key=group_config.groups.index)


def _relative_item_path(item: pytest.Item, group_config: GroupConfig) -> Path:
    item_path = Path(getattr(item, "path", getattr(item, "fspath", "")))
    if not item_path.is_absolute():
        return item_path
    try:
        return item_path.relative_to(group_config.rootpath)
    except ValueError:
        return item_path


def _configure_runtime_barrier(
    config: pytest.Config,
    group_config: GroupConfig,
    assignments: dict[str, GroupAssignment],
) -> None:
    if not hasattr(config, "workerinput"):
        return
    run_uid = str(config.workerinput.get("testrunuid") or "default")  # type: ignore[attr-defined]
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


def _initialize_barrier_state(state_path: Path, groups: list[str], expected: dict[str, int]) -> None:
    with _barrier_lock(state_path):
        if state_path.exists():
            return
        state: _BarrierState = {
            "groups": groups,
            "expected": expected,
            "finished": dict.fromkeys(groups, 0),
            "finished_nodeids": [],
        }
        _write_barrier_state(
            state_path,
            state,
        )


def _previous_groups_finished(state: _BarrierState, assignment: GroupAssignment) -> bool:
    groups = state["groups"]
    expected = state["expected"]
    finished = state["finished"]
    for group_name in groups[: assignment.ordinal - 1]:
        if int(finished.get(group_name, 0)) < int(expected.get(group_name, 0)):
            return False
    return True


def _record_barrier_finish(state_path: Path, assignment: GroupAssignment) -> None:
    with _barrier_lock(state_path):
        state = _read_barrier_state(state_path)
        finished_nodeids = set(state["finished_nodeids"])
        if assignment.item_nodeid in finished_nodeids:
            return
        finished = state["finished"]
        finished[assignment.group_name] = int(finished.get(assignment.group_name, 0)) + 1
        finished_nodeids.add(assignment.item_nodeid)
        state["finished"] = finished
        state["finished_nodeids"] = sorted(finished_nodeids)
        _write_barrier_state(state_path, state)


def _read_barrier_state(state_path: Path) -> _BarrierState:
    if not state_path.exists():
        return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {"groups": [], "expected": {}, "finished": {}, "finished_nodeids": []}
    return {
        "groups": _coerce_string_list(payload.get("groups")),
        "expected": _coerce_int_mapping(payload.get("expected")),
        "finished": _coerce_int_mapping(payload.get("finished")),
        "finished_nodeids": _coerce_string_list(payload.get("finished_nodeids")),
    }


def _coerce_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _coerce_int_mapping(value: object) -> dict[str, int]:
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


def _write_barrier_state(state_path: Path, state: _BarrierState) -> None:
    temp_path = state_path.with_suffix(f".{os.getpid()}.tmp")
    temp_path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    temp_path.replace(state_path)


def _is_terminal_report(report: pytest.TestReport) -> bool:
    if report.when == "call":
        return True
    return report.when == "setup" and (report.failed or report.skipped)


@contextmanager
def _barrier_lock(state_path: Path) -> Iterator[None]:
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
        lock_path.rmdir()
