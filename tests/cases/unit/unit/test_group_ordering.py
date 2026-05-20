"""Provide test group ordering helpers."""

from __future__ import annotations

from pathlib import Path

import pytest
from attrs import frozen

from pytest_bdd.util.tests_group_ordering import (
    GroupAssignment,
    GroupConfig,
    GroupPathMapping,
    apply_group_ordering,
    apply_order_marker,
    read_group_config,
    register_group_config_options,
    resolve_group_assignment,
)

pytestmark = [pytest.mark.unit]

pytest_plugins = ("pytester",)
REPO_SRC = Path(__file__).parents[2] / "src"


@frozen
class FakeMarker:
    """Represent fake marker state."""

    name: str
    args: tuple[object, ...] = ()


@frozen
class FakeNode:
    """Represent fake node state."""

    source: str
    own_markers: list[FakeMarker]


class FakeParser:
    """Represent fake parser state."""

    def __init__(self) -> None:
        """Initialize the fake parser."""
        self.ini_options: dict[str, tuple[str, str | None, str | None]] = {}

    def addini(self, name: str, help_text: str, **kwargs: str | None) -> None:
        """Handle addini."""
        self.ini_options[name] = (help_text, kwargs.get("type"), kwargs.get("default"))


class FakeConfig:
    """Represent fake config state."""

    def __init__(self, rootpath: Path, ini: dict[str, object]) -> None:
        """Initialize the fake config."""
        self.rootpath = rootpath
        self._ini = ini
        self.marker_lines: list[str] = []

    def getini(self, name: str) -> object:
        """Handle getini."""
        return self._ini.get(name, [] if name in {"test_group_order", "test_group_paths"} else "")

    def addinivalue_line(self, name: str, line: str) -> None:
        """Handle addinivalue line."""
        if name == "markers":
            self.marker_lines.append(line)


class FakeItem:
    """
    Represent fake item state.

    Yields:
        Generated values.

    """

    def __init__(
        self,
        path: Path,
        nodeid: str | None = None,
        marker_layers: list[tuple[str, list[str]]] | None = None,
    ) -> None:
        """Initialize the fake item."""
        self.path = path
        self.nodeid = nodeid or path.as_posix()
        self._marker_layers = [
            FakeNode(source, [FakeMarker(name) for name in names]) for source, names in (marker_layers or [])
        ]
        self.added_markers: list[FakeMarker] = []

    def iter_markers_with_node(self, name: str | None = None):
        """
        Yield markers with node.

        Yields:
            Generated values.

        """
        for node in self._marker_layers:
            for marker in node.own_markers:
                if name is None or marker.name == name:
                    yield node, marker
        for marker in self.added_markers:
            if name is None or marker.name == name:
                yield self, marker

    def iter_markers(self, name: str | None = None):
        """Yield markers."""
        return [marker for _, marker in self.iter_markers_with_node(name=name)]

    def add_marker(self, marker) -> None:
        """Handle add marker."""
        mark = getattr(marker, "mark", marker)
        self.added_markers.append(FakeMarker(mark.name, tuple(mark.args)))


def _group_config(rootpath: Path) -> GroupConfig:
    return GroupConfig(
        groups=["instant", "fast", "medium", "slow", "external"],
        default="fast",
        paths=[
            GroupPathMapping("tests/unit/**", "instant"),
            GroupPathMapping("tests/integration/**", "medium"),
            GroupPathMapping("tests/integration/slow/**", "slow"),
        ],
        rootpath=rootpath,
    )


def test_register_group_config_options_adds_pytest_ini_keys() -> None:
    """Verify register group config options adds pytest ini keys."""
    parser = FakeParser()

    register_group_config_options(parser)  # type: ignore[arg-type]

    assert parser.ini_options["test_group_order"][1] in {"args", "linelist"}
    assert parser.ini_options["test_group_default"][1] is None
    assert parser.ini_options["test_group_paths"][1] == "linelist"


def test_read_group_config_parses_pytest_ini_options(tmp_path: Path) -> None:
    """Verify read group config parses pytest ini options."""
    config = FakeConfig(
        tmp_path,
        {
            "test_group_order": ["alpha", "beta", "gamma"],
            "test_group_default": "beta",
            "test_group_paths": ["tests/a/** = alpha", "tests/c/** = gamma"],
        },
    )

    group_config = read_group_config(config)  # type: ignore[arg-type]

    assert group_config.groups == ["alpha", "beta", "gamma"]
    assert group_config.default == "beta"
    assert group_config.paths == [
        GroupPathMapping("tests/a/**", "alpha"),
        GroupPathMapping("tests/c/**", "gamma"),
    ]
    assert group_config.rootpath == tmp_path


def test_read_group_config_warns_and_normalizes_invalid_ini_values(
    tmp_path: Path,
    recwarn: pytest.WarningsRecorder,
) -> None:
    """Verify read group config warns and normalizes invalid ini values."""
    config = FakeConfig(
        tmp_path,
        {
            "test_group_order": ["alpha", "skip", "alpha", "gamma"],
            "test_group_default": "missing",
            "test_group_paths": [
                "tests/a/** = alpha",
                "bad mapping",
                "tests/missing/** = missing",
            ],
        },
    )

    group_config = read_group_config(config)  # type: ignore[arg-type]

    assert group_config.groups == ["alpha", "skip", "gamma"]
    assert group_config.default == "alpha"
    assert group_config.paths == [GroupPathMapping("tests/a/**", "alpha")]
    warnings_text = "\n".join(str(warning.message) for warning in recwarn.list)
    assert "Duplicate group name 'alpha'" in warnings_text
    assert "shadows a built-in pytest marker" in warnings_text
    assert "Default group 'missing' not found" in warnings_text
    assert "Malformed path mapping 'bad mapping'" in warnings_text
    assert "Unknown group 'missing'" in warnings_text


def test_read_group_config_warns_and_uses_fallback_for_empty_group_order(
    tmp_path: Path,
    recwarn: pytest.WarningsRecorder,
) -> None:
    """Verify read group config warns and uses fallback for empty group order."""
    config = FakeConfig(tmp_path, {"test_group_order": [], "test_group_default": ""})

    group_config = read_group_config(config)  # type: ignore[arg-type]

    assert group_config.groups == ["default"]
    assert group_config.default == "default"
    assert "No test groups configured" in str(recwarn.list[0].message)


def test_resolve_group_ignores_non_group_markers_without_warnings(
    tmp_path: Path,
    recwarn: pytest.WarningsRecorder,
) -> None:
    """Verify resolve group ignores non group markers without warnings."""
    config = _group_config(tmp_path)
    item = FakeItem(
        tmp_path / "tests" / "unknown" / "test_example.py",
        marker_layers=[("test", ["skip", "xfail", "project_specific"])],
    )

    assignment = resolve_group_assignment(item, config)  # type: ignore[arg-type]

    assert assignment.group_name == "fast"
    assert assignment.resolution_source == "default"
    assert not recwarn.list


@pytest.mark.parametrize(
    ("path", "marker_layers", "expected_group", "expected_source"),
    [
        (Path("tests/fast/test_example.py"), [], "fast", "dir_convention"),
        (Path("tests/unit/test_example.py"), [], "instant", "path_pattern"),
        (Path("tests/integration/slow/test_example.py"), [], "slow", "path_pattern"),
        (
            Path("tests/unit/test_example.py"),
            [("conftest", ["medium"])],
            "medium",
            "conftest_marker",
        ),
        (
            Path("tests/unit/test_example.py"),
            [("conftest", ["medium"]), ("test", ["external"])],
            "external",
            "test_marker",
        ),
        (
            Path("tests/unknown/test_example.py"),
            [("test", ["instant", "external"])],
            "external",
            "test_marker",
        ),
        (Path("tests/unknown/test_example.py"), [], "fast", "default"),
    ],
)
def test_resolve_group_assignment_follows_full_cascade(
    tmp_path: Path,
    path: Path,
    marker_layers: list[tuple[str, list[str]]],
    expected_group: str,
    expected_source: str,
) -> None:
    """Verify resolve group assignment follows full cascade."""
    config = _group_config(tmp_path)
    item = FakeItem(tmp_path / path, marker_layers=marker_layers)

    assignment = resolve_group_assignment(item, config)  # type: ignore[arg-type]

    assert assignment.group_name == expected_group
    assert assignment.resolution_source == expected_source
    assert assignment.ordinal == config.groups.index(expected_group) + 1


def test_apply_order_marker_adds_order_mark_without_sorting(tmp_path: Path) -> None:
    """Verify apply order marker adds order mark without sorting."""
    item = FakeItem(tmp_path / "tests" / "unit" / "test_example.py")
    assignment = GroupAssignment(
        item_nodeid=item.nodeid,
        group_name="instant",
        ordinal=1,
        resolution_source="path_pattern",
    )

    apply_order_marker(item, assignment)  # type: ignore[arg-type]

    order_marks = item.iter_markers(name="order")
    assert [mark.args for mark in order_marks] == [(1,)]


def test_apply_group_ordering_applies_markers_and_does_not_sort_items(tmp_path: Path) -> None:
    """Verify apply group ordering applies markers and does not sort items."""
    config = FakeConfig(
        tmp_path,
        {
            "test_group_order": ["instant", "fast"],
            "test_group_default": "fast",
            "test_group_paths": ["tests/unit/** = instant"],
        },
    )
    fast_item = FakeItem(tmp_path / "tests" / "other" / "test_fast.py")
    instant_item = FakeItem(tmp_path / "tests" / "unit" / "test_instant.py")
    items = [fast_item, instant_item]

    apply_group_ordering(config, items)  # type: ignore[arg-type]

    assert items == [fast_item, instant_item]
    assert [mark.args for mark in fast_item.iter_markers(name="order")] == [(2,)]
    assert [mark.args for mark in instant_item.iter_markers(name="order")] == [(1,)]
    assert "instant: test group 1" in config.marker_lines
    assert "fast: test group 2" in config.marker_lines


def test_apply_group_ordering_marks_three_groups_for_ordering_and_selection(tmp_path: Path) -> None:
    """Verify apply group ordering marks three groups for ordering and selection."""
    config = FakeConfig(
        tmp_path,
        {
            "test_group_order": ["alpha", "beta", "gamma"],
            "test_group_default": "beta",
            "test_group_paths": ["tests/alpha/** = alpha", "tests/gamma/** = gamma"],
        },
    )
    alpha_item = FakeItem(tmp_path / "tests" / "alpha" / "test_example.py")
    beta_item = FakeItem(tmp_path / "tests" / "other" / "test_example.py")
    gamma_item = FakeItem(tmp_path / "tests" / "gamma" / "test_example.py")

    apply_group_ordering(config, [gamma_item, beta_item, alpha_item])  # type: ignore[arg-type]

    assert [mark.args for mark in alpha_item.iter_markers(name="order")] == [(1,)]
    assert [mark.args for mark in beta_item.iter_markers(name="order")] == [(2,)]
    assert [mark.args for mark in gamma_item.iter_markers(name="order")] == [(3,)]
    assert [mark.name for mark in alpha_item.iter_markers(name="alpha")] == ["alpha"]
    assert [mark.name for mark in beta_item.iter_markers(name="beta")] == ["beta"]
    assert [mark.name for mark in gamma_item.iter_markers(name="gamma")] == ["gamma"]


def _write_runtime_order_project(pytester: pytest.Pytester, test_module: str) -> Path:
    event_file = pytester.path / "events.txt"
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        addopts = "--order-scope=session"
        markers = [
          "first: first test group",
          "second: second test group",
          "third: third test group",
          "order: execution ordering marker from pytest-order",
        ]
        test_group_order = ["first", "second", "third"]
        test_group_default = "second"
        test_group_paths = [
          "test_first.py = first",
          "test_second.py = second",
          "test_third.py = third",
        ]
        """,
    )
    pytester.makeconftest(
        f"""
        import sys

        sys.path.insert(0, {REPO_SRC.as_posix()!r})

        from pytest_bdd.util.tests_group_ordering import (
            apply_group_ordering,
            record_group_barrier_report,
            register_group_config_options,
            wait_for_group_barrier,
        )

        def pytest_addoption(parser):
            register_group_config_options(parser)

        def pytest_collection_modifyitems(config, items):
            apply_group_ordering(config, items)

        def pytest_runtest_setup(item):
            wait_for_group_barrier(item)

        def pytest_runtest_logreport(report):
            record_group_barrier_report(report)
        """,
    )
    pytester.makepyfile(
        test_first=test_module.format(group="first", event_file=event_file.as_posix()),
        test_second=test_module.format(group="second", event_file=event_file.as_posix()),
        test_third=test_module.format(group="third", event_file=event_file.as_posix()),
    )
    return event_file


def test_runtime_order_continues_after_failure_and_skipped_group(pytester: pytest.Pytester) -> None:
    """Verify runtime order continues after failure and skipped group."""
    event_file = _write_runtime_order_project(
        pytester,
        """
        from pathlib import Path
        import pytest

        def test_{group}_one():
            with Path("{event_file}").open("a", encoding="utf-8") as event_stream:
                event_stream.write("{group}\\n")
            if "{group}" == "first":
                pytest.fail("first group failure should not stop later groups")
            if "{group}" == "second":
                pytest.skip("second group is skipped")
        """,
    )

    result = pytester.runpytest("-q", "-s")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert event_file.read_text(encoding="utf-8").splitlines() == ["first", "second", "third"]
    result.assert_outcomes(failed=1, skipped=1, passed=1)


def test_fixture_skip_preserves_later_group_execution(pytester: pytest.Pytester) -> None:
    """Verify fixture skip preserves later group execution."""
    event_file = pytester.path / "events.txt"
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        addopts = "--order-scope=session"
        markers = [
          "first: first test group",
          "second: second test group",
          "order: execution ordering marker from pytest-order",
        ]
        test_group_order = ["first", "second"]
        test_group_default = "second"
        test_group_paths = [
          "test_first.py = first",
          "test_second.py = second",
        ]
        """,
    )
    pytester.makeconftest(
        f"""
        from pathlib import Path
        import sys
        import pytest

        sys.path.insert(0, {REPO_SRC.as_posix()!r})

        from pytest_bdd.util.tests_group_ordering import apply_group_ordering, register_group_config_options

        def pytest_addoption(parser):
            register_group_config_options(parser)

        def pytest_collection_modifyitems(config, items):
            apply_group_ordering(config, items)

        @pytest.fixture
        def skip_in_fixture():
            with Path("{event_file.as_posix()}").open("a", encoding="utf-8") as event_stream:
                event_stream.write("first-fixture\\n")
            pytest.skip("fixture skip")
        """,
    )
    pytester.makepyfile(
        test_first="""
        def test_first(skip_in_fixture):
            raise AssertionError("fixture should skip before call")
        """,
        test_second=f"""
        from pathlib import Path

        def test_second():
            with Path("{event_file.as_posix()}").open("a", encoding="utf-8") as event_stream:
                event_stream.write("second\\n")
        """,
    )

    result = pytester.runpytest("-q", "-s")

    assert result.ret == pytest.ExitCode.OK
    assert event_file.read_text(encoding="utf-8").splitlines() == ["first-fixture", "second"]
    result.assert_outcomes(skipped=1, passed=1)


def test_xdist_runtime_barrier_delays_later_group_until_earlier_group_finishes(pytester: pytest.Pytester) -> None:
    """Verify xdist runtime barrier delays later group until earlier group finishes."""
    event_file = _write_runtime_order_project(
        pytester,
        """
        from pathlib import Path
        import time

        def test_{group}_one():
            path = Path("{event_file}")
            with path.open("a", encoding="utf-8") as event_stream:
                event_stream.write("{group}:start:" + str(time.monotonic()) + "\\n")
            if "{group}" == "first":
                time.sleep(0.3)
            with path.open("a", encoding="utf-8") as event_stream:
                event_stream.write("{group}:finish:" + str(time.monotonic()) + "\\n")
        """,
    )

    result = pytester.runpytest("-q", "-s", "-n", "2")

    assert result.ret == pytest.ExitCode.OK
    observations = [
        (group, event, float(timestamp))
        for group, event, timestamp in (line.split(":") for line in event_file.read_text(encoding="utf-8").splitlines())
    ]
    first_finishes = [timestamp for group, event, timestamp in observations if group == "first" and event == "finish"]
    later_starts = [timestamp for group, event, timestamp in observations if group != "first" and event == "start"]
    assert first_finishes
    assert later_starts
    assert min(later_starts) >= max(first_finishes)


def test_marker_filter_selects_one_group_and_empty_selection_exits_cleanly(pytester: pytest.Pytester) -> None:
    """Verify marker filter selects one group and empty selection exits cleanly."""
    pytester.makepyprojecttoml(
        """
        [tool.pytest.ini_options]
        addopts = "--order-scope=session"
        markers = [
          "alpha: alpha test group",
          "beta: beta test group",
          "gamma: gamma test group",
          "order: execution ordering marker from pytest-order",
        ]
        test_group_order = ["alpha", "beta", "gamma"]
        test_group_default = "beta"
        test_group_paths = [
          "test_alpha.py = alpha",
          "test_beta.py = beta",
        ]
        """,
    )
    pytester.makeconftest(
        f"""
        import sys

        sys.path.insert(0, {REPO_SRC.as_posix()!r})

        from pytest_bdd.util.tests_group_ordering import apply_group_ordering, register_group_config_options

        def pytest_addoption(parser):
            register_group_config_options(parser)

        def pytest_collection_modifyitems(config, items):
            apply_group_ordering(config, items)
        """,
    )
    pytester.makepyfile(
        test_alpha="def test_alpha(): pass",
        test_beta="def test_beta(): pass",
    )

    selected = pytester.runpytest("-q", "-s", "-m", "alpha")
    empty = pytester.runpytest("-q", "-s", "-m", "gamma")

    assert selected.ret == pytest.ExitCode.OK
    selected.assert_outcomes(passed=1, deselected=1)
    assert empty.ret == pytest.ExitCode.NO_TESTS_COLLECTED
    empty.assert_outcomes(deselected=2)
