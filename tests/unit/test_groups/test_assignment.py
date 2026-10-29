from __future__ import annotations

from pytest_cuke.test_groups.assignment import TestGroupAssignmentSource, assign_test_group
from pytest_cuke.test_groups.config import parse_test_group_configuration


def test_item_marker_wins_and_later_configured_marker_has_priority() -> None:
    config = parse_test_group_configuration(order=("unit", "contract", "e2e"), default_group="unit")

    assignment = assign_test_group(
        config,
        nodeid="tests/misc/test_case.py::test_case",
        relative_path="tests/misc/test_case.py",
        item_markers=("slow", "unit", "e2e"),
        conftest_markers=("contract",),
    )

    assert assignment is not None
    assert assignment.group == "e2e"
    assert assignment.ordinal == 2
    assert assignment.source is TestGroupAssignmentSource.ITEM_MARKER
    assert assignment.nodeid == "tests/misc/test_case.py::test_case"


def test_conftest_marker_beats_path_mapping_and_path_mapping_beats_directory() -> None:
    config = parse_test_group_configuration(
        order=("unit", "contract", "e2e"),
        paths=("tests/unit/** = e2e", "tests/unit/** = contract"),
    )

    marker_assignment = assign_test_group(
        config,
        nodeid="tests/unit/test_marked.py::test_marked",
        relative_path="tests/unit/test_marked.py",
        conftest_markers=("contract",),
    )
    mapping_assignment = assign_test_group(
        config,
        nodeid="tests/unit/test_path.py::test_path",
        relative_path="tests/unit/test_path.py",
    )

    assert marker_assignment is not None
    assert marker_assignment.group == "contract"
    assert marker_assignment.source is TestGroupAssignmentSource.CONFTEST_MARKER
    assert mapping_assignment is not None
    assert mapping_assignment.group == "contract"
    assert mapping_assignment.source is TestGroupAssignmentSource.PATH_MAPPING


def test_directory_uses_first_configured_group_and_default_handles_other_paths() -> None:
    config = parse_test_group_configuration(order=("unit", "contract", "e2e"), default_group="contract")

    directory_assignment = assign_test_group(
        config,
        nodeid="tests/unit/e2e/test_case.py::test_case",
        relative_path="tests/unit/e2e/test_case.py",
        item_markers=("slow",),
    )
    default_assignment = assign_test_group(
        config,
        nodeid="tests/misc/test_case.py::test_case",
        relative_path="tests/misc/test_case.py",
    )

    assert directory_assignment is not None
    assert directory_assignment.group == "unit"
    assert directory_assignment.source is TestGroupAssignmentSource.DIRECTORY
    assert default_assignment is not None
    assert default_assignment.group == "contract"
    assert default_assignment.source is TestGroupAssignmentSource.DEFAULT


def test_disabled_configuration_has_no_assignment() -> None:
    config = parse_test_group_configuration(order=None)

    assert (
        assign_test_group(
            config,
            nodeid="tests/unit/test_case.py::test_case",
            relative_path="tests/unit/test_case.py",
            item_markers=("unit",),
        )
        is None
    )
