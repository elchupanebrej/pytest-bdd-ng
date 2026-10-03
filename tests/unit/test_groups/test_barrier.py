from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pytest_cuke.test_groups.assignment import TestGroupAssignment, TestGroupAssignmentSource
from pytest_cuke.test_groups.barrier import (
    TestGroupBarrier,
    TestGroupBarrierTimeout,
    _write_json_atomically,
)
from pytest_cuke.test_groups.plugin import TestGroupPlugin


def _assignment(nodeid: str, group: str, ordinal: int) -> TestGroupAssignment:
    return TestGroupAssignment(
        nodeid=nodeid,
        group=group,
        ordinal=ordinal,
        source=TestGroupAssignmentSource.DEFAULT,
    )


def test_barrier_waits_for_receipt_and_deduplicates_terminal_reports(tmp_path: Path) -> None:
    barrier = TestGroupBarrier(tmp_path / "run-a", timeout=0.1, groups=("unit", "integration"))
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    barrier.initialize((unit, integration))

    with pytest.raises(TestGroupBarrierTimeout, match=r"unit.*integration"):
        barrier.wait_for_earlier_groups(integration)

    barrier.record_terminal(unit.nodeid)
    barrier.record_terminal(unit.nodeid)
    barrier.wait_for_earlier_groups(integration)

    receipt_files = tuple((tmp_path / "run-a" / "receipts").glob("*.json"))
    assert len(receipt_files) == 1
    assert json.loads(receipt_files[0].read_text(encoding="utf-8"))["nodeid"] == unit.nodeid


def test_barrier_state_isolated_by_run_directory(tmp_path: Path) -> None:
    unit = _assignment("tests/test_unit.py::test_unit", "unit", 0)
    integration = _assignment("tests/test_integration.py::test_integration", "integration", 1)
    first = TestGroupBarrier(tmp_path / "run-a", timeout=0.02, groups=("unit", "integration"))
    second = TestGroupBarrier(tmp_path / "run-b", timeout=0.02, groups=("unit", "integration"))
    first.initialize((unit, integration))
    second.initialize((unit, integration))
    first.record_terminal(unit.nodeid)

    first.wait_for_earlier_groups(integration)
    with pytest.raises(TestGroupBarrierTimeout, match="unit"):
        second.wait_for_earlier_groups(integration)


def test_empty_selection_does_not_create_barrier_state(tmp_path: Path) -> None:
    state_dir = tmp_path / "empty-run"
    barrier = TestGroupBarrier(state_dir, timeout=1, groups=("unit", "integration"))

    barrier.initialize(())

    assert not state_dir.exists()


def test_atomic_state_replace_retries_transient_permission_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pytest_cuke.test_groups.barrier as barrier_module

    target = tmp_path / "state.json"
    replace = barrier_module.os.replace
    calls = 0

    def transient_replace(source: str | bytes | Path, destination: str | bytes | Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError(13, "file is temporarily in use")
        replace(source, destination)

    monkeypatch.setattr(barrier_module.os, "replace", transient_replace)
    _write_json_atomically(target, {"published": True})

    assert calls == 2
    assert json.loads(target.read_text(encoding="utf-8")) == {"published": True}


@pytest.mark.parametrize(
    ("when", "outcome", "should_record"),
    [
        ("call", "passed", True),
        ("call", "failed", True),
        ("call", "skipped", True),
        ("call", "rerun", False),
        ("setup", "failed", True),
        ("setup", "skipped", True),
        ("setup", "passed", False),
    ],
)
def test_plugin_records_only_terminal_reports(when: str, outcome: str, should_record: bool) -> None:
    plugin = object.__new__(TestGroupPlugin)
    recorded: list[str] = []
    plugin.barrier = SimpleNamespace(record_terminal=recorded.append)

    plugin.pytest_runtest_logreport(SimpleNamespace(when=when, outcome=outcome, nodeid="test-id"))

    assert recorded == (["test-id"] if should_record else [])


def test_plugin_rejects_remote_xdist_specs_before_worker_setup() -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True)

    with pytest.raises(pytest.UsageError, match="shared filesystem"):
        plugin.pytest_xdist_setupnodes([SimpleNamespace(popen=False, ssh="invalid.invalid")])


def test_plugin_allows_local_popen_xdist_specs() -> None:
    plugin = object.__new__(TestGroupPlugin)
    plugin.group_configuration = SimpleNamespace(enabled=True)

    plugin.pytest_xdist_setupnodes([SimpleNamespace(popen=True)])
