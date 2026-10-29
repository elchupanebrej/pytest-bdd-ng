from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from warnings import warn

import pytest

from pytest_cuke.compatibility.pytest import Parser, get_config_root_path
from pytest_cuke.compatibility.pytest import fail as pytest_fail
from pytest_cuke.test_groups.assignment import TestGroupAssignment, assign_test_group
from pytest_cuke.test_groups.barrier import TestGroupBarrier, TestGroupBarrierTimeout
from pytest_cuke.test_groups.config import parse_test_group_configuration

if TYPE_CHECKING:
    from collections.abc import Generator


def add_test_group_ini(parser: Parser) -> None:
    """Register optional suite-level test group settings."""
    parser.addini(
        "cuke_test_group_order",
        "Configured pytest test groups in execution order; a non-empty value enables group ordering.",
        default=[],
        type="linelist",
    )
    parser.addini(
        "cuke_test_group_default",
        "Default suite test group when no marker, path mapping, or directory convention matches.",
        default="",
        type="string",
    )
    parser.addini(
        "cuke_test_group_paths",
        "Relative test path mappings in GLOB = GROUP form; the last matching line wins.",
        default=[],
        type="linelist",
    )
    parser.addini(
        "cuke_test_group_barrier_timeout",
        "Maximum seconds a local xdist worker waits for earlier test groups to settle.",
        default="60",
        type="string",
    )


class TestGroupPlugin:
    """Assign optional test groups, preserve collection order, and coordinate local xdist."""

    __test__ = False

    def __init__(self, config: Any) -> None:
        try:
            self.group_configuration = parse_test_group_configuration(
                order=config.getini("cuke_test_group_order"),
                default_group=config.getini("cuke_test_group_default"),
                paths=config.getini("cuke_test_group_paths"),
                barrier_timeout=config.getini("cuke_test_group_barrier_timeout"),
            )
        except ValueError as error:
            raise pytest.UsageError(str(error)) from error

        self.config = config
        self.assignments: dict[str, TestGroupAssignment] = {}
        self.barrier: TestGroupBarrier | None = None
        self._worker = isinstance(getattr(config, "workerinput", None), dict)

        for warning in self.group_configuration.warnings:
            config_warning = getattr(config, "issue_config_time_warning", None)
            if config_warning is None:
                warn(pytest.PytestWarning(warning), stacklevel=2)
            else:
                config_warning(pytest.PytestWarning(warning), stacklevel=2)

        if self.group_configuration.enabled:
            self._register_group_markers()
            self._reject_unsupported_xdist_modes()

    @pytest.hookimpl(hookwrapper=True, tryfirst=True)
    def pytest_collection_modifyitems(self, session: Any, config: Any, items: list[Any]) -> Generator[None, None, None]:
        """Add resolved group markers before -m filtering, then stably group selected items."""
        if not self.group_configuration.enabled:
            yield
            return

        for item in items:
            assignment = self._assignment_for(item)
            self.assignments[item.nodeid] = assignment
            if item.get_closest_marker(assignment.group) is None:
                item.add_marker(assignment.group)

        yield

    @pytest.hookimpl(trylast=True)
    def pytest_collection_finish(self, session: Any) -> None:
        """Order selected groups after collection hooks, then publish xdist assignments."""
        if not self.group_configuration.enabled:
            return

        session.items[:] = sorted(
            session.items,
            key=lambda item: self._assignment_for(item).ordinal,
        )

        if not self._worker:
            return

        assignments = [self._assignment_for(item) for item in session.items]
        if not assignments:
            return

        workerinput = self.config.workerinput
        run_uid = workerinput.get("testrunuid")
        if not isinstance(run_uid, str) or not run_uid:
            raise pytest.UsageError(
                "pytest-cuke test-group barriers require pytest-xdist to provide a per-run "
                "testrunuid; upgrade pytest-xdist or disable cuke_test_group_order."
            )
        safe_uid = "".join(char if char.isalnum() or char in "-_." else "_" for char in run_uid)
        root_path = get_config_root_path(self.config)
        state_dir = root_path / ".pytest_cache" / "pytest-cuke-test-groups" / safe_uid
        barrier = TestGroupBarrier(
            state_dir,
            timeout=self.group_configuration.barrier_timeout,
            groups=self.group_configuration.order,
        )
        barrier.initialize(assignments)
        self.barrier = barrier

    @pytest.hookimpl(optionalhook=True)
    def pytest_xdist_setupnodes(self, specs: Any) -> None:
        """Reject remote xdist transports before pytest-xdist connects to workers."""
        if not self.group_configuration.enabled:
            return
        for spec in specs:
            if not _is_local_xdist_spec(spec):
                raise pytest.UsageError(
                    "cuke_test_group_order supports only local pytest-xdist workers on a shared "
                    "filesystem; remote/non-shared --tx workers are unsupported. "
                    "Use --tx=popen or disable cuke_test_group_order."
                )

    def pytest_runtest_setup(self, item: Any) -> None:
        """Hold later groups until every selected earlier-group item has a terminal receipt."""
        if self.barrier is None:
            return
        assignment = self._assignment_for(item)
        if assignment.ordinal == 0:
            return
        try:
            self.barrier.wait_for_earlier_groups(assignment)
        except TestGroupBarrierTimeout as error:
            pytest_fail(str(error), pytrace=False)

    def pytest_runtest_logreport(self, report: Any) -> None:
        """Count final calls and setup failures/skips, ignoring retry-only reports."""
        if self.barrier is None or report.outcome == "rerun":
            return
        if report.when == "call" or (report.when == "setup" and report.outcome in {"failed", "skipped"}):
            self.barrier.record_terminal(report.nodeid)

    def _assignment_for(self, item: Any) -> TestGroupAssignment:
        existing = self.assignments.get(item.nodeid)
        if existing is not None:
            return existing

        own_markers = [marker.name for marker in item.own_markers]
        inherited_markers = [
            marker.name for node in item.listchain() if node is not item for marker in node.own_markers
        ]
        item_path = getattr(item, "path", None)
        item_path = Path(str(item.fspath)) if item_path is None else Path(item_path)
        root_path = get_config_root_path(self.config)
        try:
            relative_path = item_path.relative_to(root_path).as_posix()
        except ValueError:
            relative_path = item_path.as_posix()

        assignment = assign_test_group(
            self.group_configuration,
            nodeid=item.nodeid,
            relative_path=relative_path,
            item_markers=own_markers,
            conftest_markers=inherited_markers,
        )
        if assignment is None:
            raise RuntimeError("Enabled test-group configuration produced no assignment")
        self.assignments[item.nodeid] = assignment
        return assignment

    def _register_group_markers(self) -> None:
        registered_names = {line.split(":", 1)[0].strip() for line in self.config.getini("markers") if line.strip()}
        for group in self.group_configuration.order:
            if group not in registered_names:
                self.config.addinivalue_line("markers", f"{group}: pytest-cuke suite test group")

    def _reject_unsupported_xdist_modes(self) -> None:
        if getattr(self.config.option, "dist", None) == "each":
            raise pytest.UsageError(
                "cuke_test_group_order does not support pytest-xdist --dist=each because that mode "
                "runs duplicate collections; use a local load scheduler with a shared filesystem."
            )

        transactions = getattr(self.config.option, "tx", ()) or ()
        if isinstance(transactions, str):
            transactions = (transactions,)
        for transaction in transactions:
            value = str(transaction).strip()
            if value and not value.startswith("popen"):
                raise pytest.UsageError(
                    "cuke_test_group_order supports only local pytest-xdist workers on a shared "
                    "filesystem; remote/non-shared --tx workers are unsupported. "
                    "Use --tx=popen or disable cuke_test_group_order."
                )


def _is_local_xdist_spec(spec: Any) -> bool:
    popen = getattr(spec, "popen", None)
    if popen is not None:
        return bool(popen)
    value = str(spec)
    if "'" in value:
        value = value.split("'", 1)[1].rsplit("'", 1)[0]
    return value.startswith("popen")
