"""Template rendering and fake node runtime helpers for cucumber formatters."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

from pytest_bdd.compatibility.importlib.resources import files
from pytest_bdd.plugin.gherkin_message_reporter.session import (
    CucumberFormatterRequest,
)
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog

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

_REPO_ROOT = Path(__file__).resolve().parents[4]
_TEMPLATE_RESOURCE_DIR = files("pytest_bdd_testing").joinpath("resources", "templates", "cucumber_formatters")


def _load_support_template(template_name: str) -> str:
    return str(_TEMPLATE_RESOURCE_DIR.joinpath(template_name).read_text(encoding="utf-8"))


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

    runtime_assets = FormatterPluginCatalog.discover().render_runtime_assets(tuple(formatter_requests))
    for relative_path, rendered_asset in runtime_assets.items():
        asset_path = root_path / relative_path
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_text(rendered_asset, encoding="utf-8")

    return root_path / "render_cucumber_formatters.js", payload_specs


def install_fake_node(
    monkeypatch: MonkeyPatch,
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
