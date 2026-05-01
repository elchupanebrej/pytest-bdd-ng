from __future__ import annotations

import subprocess  # noqa: S404
import warnings
from pathlib import Path
from types import SimpleNamespace

from tests.support import cucumber_formatters


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
    fake_coverage = _FakeCoverage()
    fake_coverage_module = SimpleNamespace(Coverage=SimpleNamespace(current=lambda: fake_coverage))
    observed: dict[str, object] = {}

    def fake_run(command, **_kwargs):
        observed["coverage_running_during_subprocess"] = fake_coverage.running
        observed["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setitem(cucumber_formatters.sys.modules, "coverage", fake_coverage_module)
    monkeypatch.setattr(cucumber_formatters.subprocess, "run", fake_run)

    result = cucumber_formatters.run_pytest_via_real_entrypoint(
        SimpleNamespace(tmpdir=Path.cwd()),
        "--cucumber-summary",
    )

    assert result.returncode == 0
    assert observed["coverage_running_during_subprocess"] is False
    assert fake_coverage.events == ["stop", "start"]


def test_real_entrypoint_helper_ignores_coverage_restart_warning(monkeypatch) -> None:
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

    monkeypatch.setitem(cucumber_formatters.sys.modules, "coverage", fake_coverage_module)

    def fake_run(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cucumber_formatters.subprocess, "run", fake_run)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = cucumber_formatters.run_pytest_via_real_entrypoint(SimpleNamespace(tmpdir=Path.cwd()))

    assert result.returncode == 0
    assert fake_coverage.events == ["stop", "start"]


def test_fake_node_windows_shim_prefers_path_python_under_pypy(monkeypatch) -> None:
    monkeypatch.setattr(cucumber_formatters.sys, "implementation", SimpleNamespace(name="pypy"))
    monkeypatch.setattr(cucumber_formatters.sys, "executable", r"C:\tox\pypy\python.exe")
    monkeypatch.setattr(
        cucumber_formatters.shutil,
        "which",
        lambda executable: r"C:\Python311\python.exe" if executable == "python" else None,
    )

    assert cucumber_formatters._fake_node_python_executable() == r"C:\Python311\python.exe"
