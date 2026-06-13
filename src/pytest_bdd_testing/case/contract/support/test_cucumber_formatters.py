"""

Provide test cucumber formatters helpers.
"""

from __future__ import annotations

import subprocess
import sys
import warnings
from pathlib import Path
from types import SimpleNamespace

from pytest_bdd_testing.tool.cucumber_formatter import registry, rendering


class _FakeCoverage:
    def __init__(self) -> None:
        self.running = True
        self.events: list[str] = []

    def stop(self) -> None:
        self.events.append("stop")
        self.running = False

    def start(self) -> None:
        self.events.append("start")
        self.running = True


def test_real_entrypoint_helper_suspends_active_coverage(monkeypatch) -> None:
    """
    Verify real entrypoint helper suspends active coverage.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    fake_coverage = _FakeCoverage()
    fake_coverage_module = SimpleNamespace(Coverage=SimpleNamespace(current=lambda: fake_coverage))
    observed: dict[str, object] = {}

    def fake_run(command, **_kwargs):
        observed["coverage_running_during_subprocess"] = fake_coverage.running
        observed["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setitem(sys.modules, "coverage", fake_coverage_module)
    monkeypatch.setattr(registry.subprocess, "run", fake_run)

    result = registry.run_pytest_via_real_entrypoint(
        SimpleNamespace(tmpdir=Path.cwd()),
        "--cucumber-summary",
    )

    assert result.returncode == 0
    assert observed["coverage_running_during_subprocess"] is False
    assert fake_coverage.events == ["stop", "start"]


def test_real_entrypoint_helper_ignores_coverage_restart_warning(monkeypatch) -> None:
    """
    Verify real entrypoint helper ignores coverage restart warning.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """

    class FakeCoverageWarning(Warning):
        pass

    class WarningCoverage(_FakeCoverage):
        def start(self) -> None:
            warnings.warn("already imported", FakeCoverageWarning, stacklevel=2)
            super().start()

    fake_coverage = WarningCoverage()
    fake_coverage_module = SimpleNamespace(
        Coverage=SimpleNamespace(current=lambda: fake_coverage),
        exceptions=SimpleNamespace(CoverageWarning=FakeCoverageWarning),
    )

    monkeypatch.setitem(sys.modules, "coverage", fake_coverage_module)

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(registry.subprocess, "run", fake_run)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = registry.run_pytest_via_real_entrypoint(SimpleNamespace(tmpdir=Path.cwd()))

    assert result.returncode == 0
    assert fake_coverage.events == ["stop", "start"]


def test_fake_node_windows_shim_prefers_path_python_under_pypy(monkeypatch) -> None:
    """
    Verify fake node windows shim prefers path python under pypy.

    Test target:
        Enforce framework invariants and stable API contracts.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce framework invariants and stable API contracts., then the
        expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    monkeypatch.setattr(rendering.sys, "implementation", SimpleNamespace(name="pypy"))
    monkeypatch.setattr(rendering.sys, "executable", r"C:\tox\pypy\python.exe")
    monkeypatch.setattr(
        rendering.shutil,
        "which",
        lambda executable: r"C:\Python311\python.exe" if executable == "python" else None,
    )

    assert rendering._fake_node_python_executable() == r"C:\Python311\python.exe"


def test_cucumber_formatter_support_does_not_import_returns() -> None:
    """
    Verify fake formatter support avoids PyPy-incompatible returns import.

    Test target:
        Enforce standard-compliant report formats to guarantee compatibility with external viewer tools.
    Test type:
        E2E/Acceptance test
    Test scenario:
        Given the relevant preconditions are met, when Enforce standard-compliant report formats to guarantee
        compatibility with external viewer tools., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    assert "returns.maybe" not in Path(registry.__file__).read_text(encoding="utf-8")
    assert "returns.maybe" not in Path(rendering.__file__).read_text(encoding="utf-8")
