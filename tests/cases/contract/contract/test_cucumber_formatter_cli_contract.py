"""Provide test cucumber formatter cli contract helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import tomllib

from pytest_bdd.plugin.cucumber_json.const import CucumberJson
from pytest_bdd.plugin.gherkin_message_reporter import entrypoint as formatter_entrypoint
from pytest_bdd.plugin.gherkin_message_reporter.plugin import (
    CucumberFormatterConfigurationError,
    GherkinMessageReporter,
)
from pytest_bdd.plugin.gherkin_message_reporter.runtime_contract import ReporterLifecycleContract
from pytest_bdd.testing.cucumber_formatters import install_formatter_hook_registry
from pytest_bdd.util.cucumber_formatter_support import registry as formatter_registry
from pytest_bdd.util.cucumber_formatter_support.registry import FormatterPluginCatalog
from pytest_bdd.util.cucumber_formatters import cucumber_formatter_definitions


def _build_config(tmp_path: Path, **overrides):
    options = {
        "messages_ndjson_path": None,
        "cucumber_html_path": None,
        "cucumber_summary": False,
        "cucumber_progress": False,
        "cucumber_progress_bar": False,
        "cucumber_js_json_path": None,
        "cucumber_junit_path": None,
        "cucumber_usage_output": None,
        "cucumber_usage_json_path": None,
        "cucumber_snippets": False,
        "cucumber_pretty": False,
    }
    options.update(overrides)
    config = SimpleNamespace(option=SimpleNamespace(**options), rootpath=tmp_path)
    install_formatter_hook_registry(config, catalog=_catalog())
    return config


def _catalog() -> FormatterPluginCatalog:
    return FormatterPluginCatalog.discover()


def test_formatter_catalog_discovery_is_cached(monkeypatch) -> None:
    """Verify formatter catalog discovery is cached."""
    formatter_registry._discover_formatter_plugin_catalog.cache_clear()

    original_entry_points = formatter_registry.entry_points
    entry_point_calls = 0

    def counting_entry_points(*args, **kwargs):
        nonlocal entry_point_calls
        entry_point_calls += 1
        return original_entry_points(*args, **kwargs)

    monkeypatch.setattr(formatter_registry, "entry_points", counting_entry_points)

    try:
        first = FormatterPluginCatalog.discover()
        second = FormatterPluginCatalog.discover()
    finally:
        formatter_registry._discover_formatter_plugin_catalog.cache_clear()

    assert first is second
    assert entry_point_calls == 1


def test_collects_legal_formatter_selection(tmp_path: Path) -> None:
    """Verify collects legal formatter selection."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    reporter = GherkinMessageReporter(
        config=_build_config(
            tmp_path,
            cucumber_summary=True,
            cucumber_js_json_path=str(reports_dir / "report.json"),
            cucumber_usage_json_path=str(reports_dir / "usage.json"),
        ),
    )

    assert [request.formatter for request in reporter.requested_cucumber_formatters] == [
        "summary",
        "json",
        "usage-json",
    ]
    assert reporter.live_formatters == reporter.requested_cucumber_formatters
    assert reporter.deferred_formatters == ()
    assert reporter.requested_cucumber_formatters[0].output_path is None
    assert reporter.requested_cucumber_formatters[1].output_path == (reports_dir / "report.json").resolve()
    assert reporter.requested_cucumber_formatters[2].output_path == (reports_dir / "usage.json").resolve()


def test_rejects_multiple_terminal_output_formatters(tmp_path: Path) -> None:
    """Verify rejects multiple terminal output formatters."""
    with pytest.raises(
        CucumberFormatterConfigurationError,
        match="Only one terminal-output formatter may be active per run",
    ):
        GherkinMessageReporter(
            config=_build_config(
                tmp_path,
                cucumber_summary=True,
                cucumber_progress=True,
            ),
        )


def test_rejects_missing_output_directory(tmp_path: Path) -> None:
    """Verify rejects missing output directory."""
    missing_path = tmp_path / "missing" / "report.json"

    with pytest.raises(
        CucumberFormatterConfigurationError,
        match="Formatter output directory does not exist",
    ):
        GherkinMessageReporter(
            config=_build_config(
                tmp_path,
                cucumber_js_json_path=str(missing_path),
            ),
        )


def test_rejects_duplicate_file_output_paths(tmp_path: Path) -> None:
    """Verify rejects duplicate file output paths."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    duplicate_path = reports_dir / "report.out"

    with pytest.raises(
        CucumberFormatterConfigurationError,
        match="Multiple formatter outputs target the same path",
    ):
        GherkinMessageReporter(
            config=_build_config(
                tmp_path,
                cucumber_js_json_path=str(duplicate_path),
                cucumber_junit_path=str(duplicate_path),
            ),
        )


def test_legacy_cucumber_json_option_destination_remains_separate() -> None:
    """Verify legacy cucumber json option destination remains separate."""
    legacy_dest = str(CucumberJson.Cli.PATH_OPTION)
    formatter_option_attrs = {definition[0] for definition in cucumber_formatter_definitions()}

    assert legacy_dest not in formatter_option_attrs


def test_formatter_registry_maps_requests_to_dedicated_plugin_modules(tmp_path: Path) -> None:
    """Verify formatter registry maps requests to dedicated plugin modules."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    reporter = GherkinMessageReporter(
        config=_build_config(
            tmp_path,
            cucumber_summary=True,
            cucumber_junit_path=str(reports_dir / "report.xml"),
        ),
    )

    registry_modules = {plugin.formatter: plugin.module_name for plugin in _catalog().plugins}

    assert reporter.requested_cucumber_formatters[0].plugin_module == registry_modules["summary"]
    assert reporter.requested_cucumber_formatters[1].plugin_module == registry_modules["junit"]


def test_formatter_plugins_live_in_sibling_plugin_package() -> None:
    """Verify formatter plugins live in sibling plugin package."""
    for plugin in _catalog().plugins:
        assert plugin.module_name.startswith("pytest_bdd.plugin.cucumber_")
        assert ".cucumber_formatter_support." not in plugin.module_name
        assert ".gherkin_message_reporter." not in plugin.module_name


def test_formatter_plugins_expose_pytest_hookimpls() -> None:
    """Verify formatter plugins expose pytest hookimpls."""
    for plugin in _catalog().plugins:
        assert getattr(plugin.pytest_addoption, "pytest_impl", None) is not None
        assert getattr(plugin.pytest_bdd_cucumber_formatter_request, "pytest_impl", None) is not None
        assert getattr(plugin.pytest_bdd_cucumber_formatter_runtime_assets, "pytest_impl", None) is not None


def test_entrypoint_addhooks_only_registers_hookspecs() -> None:
    """Verify entrypoint addhooks only registers hookspecs."""

    class _PluginManager:
        def __init__(self) -> None:
            self.registered: list[tuple[object, str | None]] = []
            self.added_hookspecs: list[object] = []

        def register(self, plugin, name=None) -> None:
            self.registered.append((plugin, name))

        def add_hookspecs(self, hookspecs) -> None:
            self.added_hookspecs.append(hookspecs)

    pluginmanager = _PluginManager()
    formatter_entrypoint.pytest_addhooks(pluginmanager)

    assert pluginmanager.added_hookspecs
    assert pluginmanager.registered == []


def test_formatter_plugins_have_independent_pytest11_entrypoints() -> None:
    """Verify formatter plugins have independent pytest11 entrypoints."""
    pyproject_path = Path(__file__).resolve().parents[4] / "pyproject.toml"
    pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    pytest11_entrypoints = pyproject["project"]["entry-points"]["pytest11"]

    for plugin in _catalog().plugins:
        assert pytest11_entrypoints[plugin.plugin_name] == plugin.plugin_entrypoint_target


def test_runtime_session_resolves_formatter_requests_via_hooks_not_entrypoint_registry() -> None:
    """Verify runtime session resolves formatter requests via hooks not entrypoint registry."""
    session_source = (
        Path(__file__).resolve().parents[4]
        / "src"
        / "pytest_bdd"
        / "plugin"
        / "gherkin_message_reporter"
        / "session.py"
    ).read_text(encoding="utf-8")

    assert "cucumber_formatter_support.registry" not in session_source
    assert "pytest_bdd_cucumber_formatter_request" in session_source
    assert "pytest_bdd_cucumber_formatter_runtime_assets" in session_source


def test_reporter_implements_explicit_lifecycle_contract(tmp_path: Path) -> None:
    """Verify reporter implements explicit lifecycle contract."""
    reporter = GherkinMessageReporter(config=_build_config(tmp_path, cucumber_summary=True))

    assert isinstance(reporter, ReporterLifecycleContract)


def test_entrypoint_source_does_not_fall_back_to_private_reporter_methods() -> None:
    """Verify entrypoint source does not fall back to private reporter methods."""
    entrypoint_source = (
        Path(__file__).resolve().parents[4]
        / "src"
        / "pytest_bdd"
        / "plugin"
        / "gherkin_message_reporter"
        / "entrypoint.py"
    ).read_text(encoding="utf-8")

    assert "_start_live_formatters" not in entrypoint_source
    assert "_restore_terminal_reporter" not in entrypoint_source
    assert "duck typing" not in entrypoint_source
