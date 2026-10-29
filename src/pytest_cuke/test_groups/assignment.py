from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatchcase
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_cuke.test_groups.config import TestGroupConfiguration


class TestGroupAssignmentSource(str, Enum):
    """The rule that selected a test's configured group."""

    __test__ = False

    ITEM_MARKER = "item-marker"
    CONFTEST_MARKER = "conftest-marker"
    PATH_MAPPING = "path-mapping"
    DIRECTORY = "directory"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class TestGroupAssignment:
    """Stable resolution metadata consumed by scheduling and barrier code."""

    __test__ = False

    group: str
    ordinal: int
    source: TestGroupAssignmentSource
    nodeid: str


def assign_test_group(
    configuration: TestGroupConfiguration,
    *,
    nodeid: str,
    relative_path: str,
    item_markers: Iterable[str] = (),
    conftest_markers: Iterable[str] = (),
) -> TestGroupAssignment | None:
    """Resolve a stable group assignment using the public precedence cascade.

    Valid item-level group markers win over conftest markers. Within either
    marker scope, the latest group in configured order wins. Path mappings use
    last-match-wins; directory conventions then choose the first configured
    group found in a relative directory component, before the default.
    """
    if not configuration.enabled:
        return None

    item_group = _latest_configured_group(configuration, item_markers)
    if item_group is not None:
        return _assignment(configuration, item_group, TestGroupAssignmentSource.ITEM_MARKER, nodeid)

    conftest_group = _latest_configured_group(configuration, conftest_markers)
    if conftest_group is not None:
        return _assignment(configuration, conftest_group, TestGroupAssignmentSource.CONFTEST_MARKER, nodeid)

    normalized_path = _normalize_relative_path(relative_path)
    path_group: str | None = None
    for mapping in configuration.path_mappings:
        if fnmatchcase(normalized_path, mapping.pattern):
            path_group = mapping.group
    if path_group is not None:
        return _assignment(configuration, path_group, TestGroupAssignmentSource.PATH_MAPPING, nodeid)

    directories = PurePosixPath(normalized_path).parts[:-1]
    for group in configuration.order:
        if group in directories:
            return _assignment(configuration, group, TestGroupAssignmentSource.DIRECTORY, nodeid)

    default_group = configuration.default_group or configuration.order[0]
    return _assignment(configuration, default_group, TestGroupAssignmentSource.DEFAULT, nodeid)


def _latest_configured_group(configuration: TestGroupConfiguration, markers: Iterable[str]) -> str | None:
    applied = set(markers)
    return next((group for group in reversed(configuration.order) if group in applied), None)


def _normalize_relative_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _assignment(
    configuration: TestGroupConfiguration,
    group: str,
    source: TestGroupAssignmentSource,
    nodeid: str,
) -> TestGroupAssignment:
    return TestGroupAssignment(
        group=group,
        ordinal=configuration.ordinal(group),
        source=source,
        nodeid=nodeid,
    )
