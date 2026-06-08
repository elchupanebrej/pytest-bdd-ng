"""Formatter registry, test helpers, and assertion utilities for cucumber formatters."""

from __future__ import annotations

import json
import os
import subprocess  # noqa: S404
import sys
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

from pytest_bdd.util.cucumber_formatters import (
    pytest_capture_already_configured,
    terminal_formatter_flags_requested,
)

_SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS = (
    "test session starts",
    "platform ",
    "rootdir:",
    "collected ",
    "short test summary info",
    " passed in ",
)

_VISIBLE_PYTEST_TERMINAL_FRAGMENTS = (
    "test session starts",
    "platform ",
    "rootdir:",
    "collected ",
    "ERROR collecting ",
    "INTERNALERROR>",
)

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _active_coverage_controller() -> Any | None:
    try:
        import coverage
    except ImportError:
        return None
    current = getattr(getattr(coverage, "Coverage", None), "current", None)
    if not callable(current):
        return None
    return current()


@contextmanager
def _suspend_active_coverage() -> Generator[None, None, None]:
    controller = _active_coverage_controller()
    if controller is None:
        yield
        return
    coverage_module = sys.modules.get("coverage")
    coverage_warning = getattr(getattr(coverage_module, "exceptions", None), "CoverageWarning", Warning)
    controller.stop()
    try:
        yield
    finally:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=coverage_warning)
            controller.start()


def expected_formatter_output(formatter_name: str) -> str:
    """Handle expected formatter output."""
    from pytest_bdd_testing.cucumber_formatters.rendering import _FAKE_FORMATTER_OUTPUTS

    return _FAKE_FORMATTER_OUTPUTS[formatter_name]


def expected_formatter_output_lines(formatter_name: str) -> list[str]:
    """Handle expected formatter output lines."""
    return expected_formatter_output(formatter_name).splitlines()


def expected_formatter_visible_line(formatter_name: str) -> str:
    """Handle expected formatter visible line."""
    return expected_formatter_output_lines(formatter_name)[0]


def assert_pytest_terminal_reporter_suppressed(output: str) -> None:
    """Assert pytest terminal reporter suppressed."""
    unexpected_fragments = [fragment for fragment in _SUPPRESSED_PYTEST_TERMINAL_FRAGMENTS if fragment in output]
    assert unexpected_fragments == [], (
        f"unexpected default pytest terminal reporter output was emitted: {unexpected_fragments!r}\n{output}"
    )


def assert_pytest_terminal_reporter_visible(output: str) -> None:
    """Assert pytest terminal reporter visible."""
    visible_fragments = [fragment for fragment in _VISIBLE_PYTEST_TERMINAL_FRAGMENTS if fragment in output]
    assert visible_fragments, f"expected default pytest terminal reporter output, got:\n{output}"


def assert_formatter_output_is_not_mixed_with_pytest_terminal(output: str, *, formatter_name: str) -> None:
    """Assert formatter output is not mixed with pytest terminal."""
    assert expected_formatter_visible_line(formatter_name) in output, output
    assert_pytest_terminal_reporter_suppressed(output)


def run_pytest_via_real_entrypoint(
    testdir: Any,
    *cli_args: str,
    extra_env: dict[str, str] | None = None,
    preserve_fake_node: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run pytest via real entrypoint."""
    repo_root = _REPO_ROOT
    env = os.environ.copy()
    if not preserve_fake_node:
        capture_dir = env.pop("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", None)
        if capture_dir:
            fake_bin = Path(capture_dir).parent / "fake-node-bin"
            env["PATH"] = os.pathsep.join(
                p for p in env["PATH"].split(os.pathsep) if Path(p).resolve() != fake_bin.resolve()
            )
        env.pop("NODE_PATH", None)
        env.pop("FAKE_GLOBAL_NODE_MODULES_ROOT", None)
    for key in tuple(env):
        if key.startswith("PYTEST_") and not key.startswith("PYTEST_BDD_"):
            env.pop(key, None)
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = src_path
    if extra_env:
        env.update(extra_env)
    effective_cli_args = with_pytester_terminal_capture_disabled(*cli_args)
    with _suspend_active_coverage():
        return subprocess.run(  # noqa: S603
            [sys.executable, "-m", "pytest", *effective_cli_args],
            cwd=str(testdir.tmpdir),
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )


def requests_terminal_formatter_output(*cli_args: str) -> bool:
    """Handle requests terminal formatter output."""
    return terminal_formatter_flags_requested(cli_args)


def with_pytester_terminal_capture_disabled(*cli_args: str) -> tuple[str, ...]:
    """Handle with pytester terminal capture disabled."""
    if pytest_capture_already_configured(cli_args):
        return cli_args
    if not terminal_formatter_flags_requested(cli_args):
        return cli_args
    return ("--capture=no", *cli_args)


def enable_fake_node_capture(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """Handle enable fake node capture."""
    capture_dir = tmp_path / "fake-node-captures"
    capture_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", str(capture_dir))
    return capture_dir


def read_fake_node_captures(capture_dir: Path) -> list[dict[str, Any]]:
    """Read fake node captures."""
    return [json.loads(capture_path.read_text(encoding="utf-8")) for capture_path in sorted(capture_dir.glob("*.json"))]


def read_fake_formatter_telemetry(tmp_path: Path) -> list[dict[str, Any]]:
    """Read fake formatter telemetry."""
    telemetry: list[dict[str, Any]] = []
    for capture in read_fake_node_captures(tmp_path / "fake-node-captures"):
        source_mode = "messagesPath" if capture.get("messagesPath") else "stdin"
        normalized = {
            "sourceMode": source_mode,
            "formatterNames": capture.get("formatterNames", []),
            "envelopeCount": capture.get("envelopeCount", 0),
            "emittedVisibleOutputDuringStream": capture.get("emittedConsoleBeforeClose", False),
            "consoleWriteCount": capture.get("consoleWriteCount", 0),
            "consoleFormatterNames": capture.get("consoleFormatterNames", []),
        }
        messages_path = capture.get("messagesPath")
        if messages_path:
            normalized["messagesPath"] = messages_path
        worker_ids = capture.get("workerIds")
        if worker_ids:
            normalized["workerIds"] = worker_ids
        telemetry.append(normalized)
    return telemetry


def install_formatter_hook_registry(
    config: Any,
    *,
    catalog: Any = None,
) -> Any:
    """Handle install formatter hook registry."""
    from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog

    resolved_catalog = FormatterPluginCatalog.discover() if catalog is None else catalog

    class _HookProxy:
        def pytest_bdd_cucumber_formatter_request(
            self,
            *,
            config: Any,
            resolve_output_path: Any,
        ) -> list[dict[str, str]]:
            requests: list[dict[str, str]] = []
            for plugin in resolved_catalog.plugins:
                request = plugin.pytest_bdd_cucumber_formatter_request(
                    config=config,
                    resolve_output_path=resolve_output_path,
                )
                if request is not None:
                    requests.append(request)  # type: ignore[arg-type]  # dynamic CucumberFormatterRequest
            return requests

        def pytest_bdd_cucumber_formatter_runtime_assets(
            self,
            *,
            formatter_request: Any,
            formatter_requests: Any,
        ) -> list[dict[str, str]]:
            rendered_assets: list[dict[str, str]] = []
            for plugin in resolved_catalog.plugins:
                assets = plugin.pytest_bdd_cucumber_formatter_runtime_assets(
                    formatter_request=formatter_request,
                    formatter_requests=formatter_requests,
                )
                if assets:
                    rendered_assets.append(assets)
            return rendered_assets

    pluginmanager = getattr(config, "pluginmanager", None)
    if pluginmanager is None:
        pluginmanager = SimpleNamespace()
        config.pluginmanager = pluginmanager
    pluginmanager.hook = _HookProxy()
    return pluginmanager


def build_sample_suite(testdir: Any) -> None:
    """Build sample suite."""
    testdir.makeini(
        """\
        [pytest]
        disable_feature_autoload = true
        """,
    )
    testdir.makefile(
        ".feature",
        formatter_suite="""\
        Feature: formatter coverage

          Scenario: passing scenario
            Given a passing step

          Scenario: failing scenario
            Given a failing step
        """,
    )
    testdir.makeconftest(
        """\
        from pytest_bdd import given

        @given("a passing step")
        def _pass():
            return "ok"

        @given("a failing step")
        def _fail():
            raise RuntimeError("boom")
        """,
    )
    testdir.makepyfile(
        test_formatter_suite="""\
        from pytest_bdd import scenarios

        test_formatter_suite = scenarios("formatter_suite.feature")
        """,
    )
