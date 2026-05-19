"""Provide cucumber formatters helpers."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess  # noqa: S404
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterRequest,
)
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.util.cucumber_formatters import (
    pytest_capture_already_configured,
    terminal_formatter_flags_requested,
)

_FAKE_FORMATTER_OUTPUTS = {
    "summary": "Summary: 2 scenarios (1 passed, 1 failed)\n",
    "progress": "Progress: .F\n",
    "progress-bar": "Progress bar: .[##########] 2/2\n",
    "snippets": (
        "Snippet suggestion: missing step definition\n@given('an undefined step')\ndef an_undefined_step():\n    ...\n"
    ),
    "pretty": "Feature: formatter coverage\n  Scenario: passing scenario\n  Scenario: failing scenario\n",
    "usage": "Usage: Given a passing step x1; Given a failing step x1\n",
    "json": 'JSON formatter payload\n{"formatter": "json", "passed": 1, "failed": 1}\n',
    "junit": (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<testsuite name="pytest-bdd-ng" tests="2" failures="1">\n'
        '  <testcase name="passing scenario" classname="formatter_suite"/>\n'
        '  <testcase name="failing scenario" classname="formatter_suite">\n'
        '    <failure message="boom">RuntimeError: boom</failure>\n'
        "  </testcase>\n"
        "</testsuite>\n"
    ),
    "usage-json": (
        '{"formatter": "usage-json", "steps": [{"text": "Given a passing step", "count": 1}, '
        '{"text": "Given a failing step", "count": 1}]}\n'
    ),
}

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

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATE_DIR = _REPO_ROOT / "tests" / "assets" / "templates" / "cucumber_formatters"


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
def _suspend_active_coverage():
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
        # Strip fake node environment from previous test steps (#3213)
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
    # Real user invocations switch terminal formatters to no-capture automatically.
    # Nested child pytest runs spawned from within pytest are less stable here, so the
    # helper normalizes to the same effective CLI and leaves the auto-rewrite assertion
    # to dedicated hook/lifecycle tests.
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
    # Real user invocations switch to no-capture automatically via the reporter
    # entrypoint. Pytester subprocess mode does not reliably exercise that early
    # option-rewrite path, so normalize nested acceptance runs to the same
    # effective CLI before launching the child pytest process.
    return ("--capture=no", *cli_args)


def enable_fake_node_capture(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
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


def _load_support_template(template_name: str) -> str:
    return (_TEMPLATE_DIR / template_name).read_text(encoding="utf-8")


def _render_support_template(template_name: str, *, replacements: dict[str, str] | None = None) -> str:
    rendered = _load_support_template(template_name)
    if not replacements:
        return rendered
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def _fake_node_python_executable() -> str:
    override = os.environ.get("PYTEST_BDD_FAKE_NODE_PYTHON")
    if override:
        return override
    if sys.implementation.name == "pypy":
        python_executable = shutil.which("python")
        if python_executable and os.path.normcase(str(Path(python_executable).resolve())) != os.path.normcase(
            str(Path(sys.executable).resolve()),
        ):
            return python_executable
    return sys.executable


def _write_windows_command_shim(command_path: Path, target_script_path: Path) -> None:
    python_executable = _fake_node_python_executable()
    command_path.write_text(
        "\r\n".join(
            (
                "@echo off",
                f'"{python_executable}" "{target_script_path}" %*',
                "",
            ),
        ),
        encoding="utf-8",
    )


def _write_fake_html_formatter_assets(package_dir: Path) -> None:
    dist_dir = package_dir / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "main.js").write_text("window.CUCUMBER_HTML_FORMATTER_TEST = true;\n", encoding="utf-8")
    (dist_dir / "main.css").write_text("body { font-family: sans-serif; }\n", encoding="utf-8")
    src_dir = package_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "index.mustache.html").write_text(
        "<!doctype html><html><head><title>{{title}}</title><style>{{css}}</style></head>"
        "<body><script>window.CUCUMBER_MESSAGES=[{{messages}}];</script><script>{{script}}</script></body></html>",
        encoding="utf-8",
    )


def materialize_fake_node_runtime(
    root_path: Path,
    *,
    preinstalled_packages: tuple[str, ...] = ("@cucumber/cucumber", "@cucumber/pretty-formatter"),
) -> dict[str, Path]:
    """Handle materialize fake node runtime."""
    root_path.mkdir(parents=True, exist_ok=True)
    bin_dir = root_path / "fake-node-bin"
    bin_dir.mkdir(exist_ok=True)
    seed_node_modules = root_path / "fake-node-modules"
    seed_node_modules.mkdir(exist_ok=True)
    global_node_modules = root_path / "fake-global-node-modules"
    global_node_modules.mkdir(exist_ok=True)
    capture_dir = root_path / "fake-node-captures"
    capture_dir.mkdir(exist_ok=True)

    for package_name in preinstalled_packages:
        package_dir = seed_node_modules.joinpath(*package_name.split("/"))
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "package.json").write_text(
            json.dumps({"name": package_name, "version": "0.0.0-test"}, indent=2) + "\n",
            encoding="utf-8",
        )
        if package_name == "@cucumber/html-formatter":
            _write_fake_html_formatter_assets(package_dir)

    node_path = bin_dir / "node"
    node_path.write_text(
        _render_support_template(
            "fake_node_runtime.py.j2",
            replacements={"__FORMATTER_OUTPUTS__": repr(_FAKE_FORMATTER_OUTPUTS)},
        ),
        encoding="utf-8",
        newline="\n",
    )
    node_path.chmod(node_path.stat().st_mode | stat.S_IEXEC)

    npm_path = bin_dir / "npm"
    npm_path.write_text(
        _render_support_template("fake_npm_runtime.py.j2"),
        encoding="utf-8",
        newline="\n",
    )
    npm_path.chmod(npm_path.stat().st_mode | stat.S_IEXEC)
    _write_windows_command_shim(bin_dir / "node.cmd", node_path)
    _write_windows_command_shim(bin_dir / "npm.cmd", npm_path)
    return {
        "bin_dir": bin_dir,
        "seed_node_modules": seed_node_modules,
        "global_node_modules": global_node_modules,
        "capture_dir": capture_dir,
    }


def materialize_live_formatter_runtime(
    root_path: Path,
    *formatter_names: str,
    output_paths: dict[str, str | None] | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    """Handle materialize live formatter runtime."""
    output_paths = {} if output_paths is None else dict(output_paths)
    plugins_by_name = FormatterPluginCatalog.discover().by_name()
    formatter_requests: list[CucumberFormatterRequest] = []
    payload_specs: list[dict[str, object]] = []

    for formatter_name in formatter_names:
        plugin = plugins_by_name[formatter_name]
        output_path = output_paths.get(formatter_name)
        formatter_request = CucumberFormatterRequest(
            option_attr=plugin.option_attr,
            cli_flag=plugin.cli_flag,
            formatter=plugin.formatter,
            package_name=plugin.package_name,
            output_path=Path(output_path) if output_path is not None else None,
            plugin_module=plugin.module_name,
            runtime_kind=plugin.runtime_kind,
            runtime_specifier=plugin.runtime_specifier or plugin.formatter,
            runtime_module_path=plugin.module_runtime_path if plugin.has_module_runtime else None,
            runtime_export_name=plugin.runtime_export_name,
            runtime_template_name=plugin.module_runtime_template_name if plugin.has_module_runtime else None,
            discovery_order=plugin.discovery_order,
        )
        formatter_requests.append(formatter_request)
        payload_specs.append(
            {
                "formatter": formatter_request.formatter,
                "outputPath": output_path,
                "cliFlag": formatter_request.cli_flag,
                "runtime": {
                    "kind": formatter_request.runtime_kind.value,
                    "specifier": formatter_request.runtime_specifier,
                    "modulePath": formatter_request.runtime_module_path,
                    "exportName": formatter_request.runtime_export_name,
                },
            },
        )

    runtime_assets = FormatterPluginCatalog.discover().render_runtime_assets(formatter_requests)
    for relative_path, rendered_asset in runtime_assets.items():
        asset_path = root_path / relative_path
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_text(rendered_asset, encoding="utf-8")

    return root_path / "render_cucumber_formatters.js", payload_specs


def install_fake_node(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    preinstalled_packages: tuple[str, ...] = ("@cucumber/cucumber", "@cucumber/pretty-formatter"),
) -> None:
    """Handle install fake node."""
    runtime = materialize_fake_node_runtime(tmp_path, preinstalled_packages=preinstalled_packages)
    monkeypatch.setenv("PATH", f"{runtime['bin_dir']}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("NODE_PATH", str(runtime["seed_node_modules"]))
    monkeypatch.setenv("FAKE_GLOBAL_NODE_MODULES_ROOT", str(runtime["global_node_modules"]))
    monkeypatch.setenv("PYTEST_BDD_FAKE_NODE_CAPTURE_DIR", str(runtime["capture_dir"]))


def install_formatter_hook_registry(
    config: Any,
    *,
    catalog: FormatterPluginCatalog | None = None,
) -> Any:
    """Handle install formatter hook registry."""
    resolved_catalog = FormatterPluginCatalog.discover() if catalog is None else catalog

    class _HookProxy:
        def pytest_bdd_cucumber_formatter_request(self, *, config, resolve_output_path):
            requests: list[CucumberFormatterRequest] = []
            for plugin in resolved_catalog.plugins:
                request = plugin.pytest_bdd_cucumber_formatter_request(
                    config=config,
                    resolve_output_path=resolve_output_path,
                )
                if request is not None:
                    requests.append(request)
            return requests

        def pytest_bdd_cucumber_formatter_runtime_assets(self, *, formatter_request, formatter_requests):
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


def build_sample_suite(testdir) -> None:
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
